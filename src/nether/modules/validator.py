"""
Secure Module Validator for external web components.
Validates JavaScript modules before allowing registration.
"""

import contextlib
import hashlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import aiofiles
from aiohttp import web


@dataclass(frozen=True, kw_only=True, slots=True)
class ComponentManifest:
    """Manifest for a web component."""

    id: str
    name: str
    version: str
    author: str
    description: str
    tag_name: str
    module_url: str
    permissions: list[str]
    api_endpoints: list[str]
    signature: str | None = None
    hash: str | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class ValidationResult:
    """Result of component validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    validated_module_path: str | None = None
    security_score: int = 0


class ComponentValidator:
    """Validates external web components for security and compliance."""

    def __init__(self):
        # Allowed Web APIs
        self.allowed_apis = {
            "HTMLElement",
            "customElements",
            "fetch",
            "console",
            "document.createElement",
            "document.getElementById",
            "addEventListener",
            "removeEventListener",
            "CustomEvent",
            "DOMParser",
            "JSON",
            "Array",
            "Object",
            "String",
            "Number",
            "setTimeout",
            "setInterval",
            "clearTimeout",
            "clearInterval",
        }

        # Blocked dangerous APIs
        self.blocked_apis = {
            "eval",
            "Function",
            "document.write",
            "document.writeln",
            "innerHTML",
            "outerHTML",
            "insertAdjacentHTML",
            "execScript",
            "setTimeout",
            "setInterval",
            "XMLHttpRequest",
            "ActiveXObject",
            "importScripts",
            "Worker",
            "SharedWorker",
        }

        # Required patterns for valid components
        self.required_patterns = [
            r"class\s+\w+\s+extends\s+HTMLElement",  # Must extend HTMLElement
            r"customElements\.define\s*\(",  # Must register element
            r"connectedCallback\s*\(",  # Must have lifecycle
        ]

        # Trusted component authors (would be configurable)
        self.trusted_authors = set()

    async def validate_component(self, manifest: ComponentManifest, source_code: str) -> ValidationResult:
        """Validate a component comprehensively."""
        errors = []
        warnings = []
        security_score = 100

        try:
            # 1. Manifest validation
            manifest_errors = self._validate_manifest(manifest)
            errors.extend(manifest_errors)

            # 2. Static code analysis
            static_errors, static_warnings, static_score = self._static_analysis(source_code)
            errors.extend(static_errors)
            warnings.extend(static_warnings)
            security_score = min(security_score, static_score)

            # 3. API usage validation
            api_errors, api_score = self._validate_api_usage(source_code)
            errors.extend(api_errors)
            security_score = min(security_score, api_score)

            # 4. Security patterns check
            security_errors, security_score_delta = self._check_security_patterns(source_code)
            errors.extend(security_errors)
            security_score = min(security_score, security_score_delta)

            # 5. Syntax validation
            syntax_errors = await self._validate_syntax(source_code)
            errors.extend(syntax_errors)

            # 6. Create validated module if no critical errors
            validated_module_path = None
            if not errors and security_score >= 70:  # Minimum security threshold
                validated_module_path = await self._create_validated_module(manifest, source_code)

            return ValidationResult(
                valid=len(errors) == 0 and security_score >= 70,
                errors=errors,
                warnings=warnings,
                validated_module_path=validated_module_path,
                security_score=security_score,
            )

        except Exception as e:
            return ValidationResult(valid=False, errors=[f"Validation failed: {e!s}"], warnings=[], security_score=0)

    def _validate_manifest(self, manifest: ComponentManifest) -> list[str]:
        """Validate component manifest."""
        errors = []

        # Required fields
        if not manifest.id or not manifest.id.isalnum():
            errors.append("Module ID must be alphanumeric")

        if not manifest.tag_name or not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", manifest.tag_name):
            errors.append("Invalid tag name - must be kebab-case")

        if not manifest.author:
            errors.append("Module author is required")

        # Version validation
        if not re.match(r"^\d+\.\d+\.\d+$", manifest.version):
            errors.append("Version must follow semantic versioning (x.y.z)")

        # Permissions validation
        allowed_permissions = {"api:read", "api:write", "storage:read", "storage:write"}
        for perm in manifest.permissions:
            if perm not in allowed_permissions:
                errors.append(f"Unknown permission: {perm}")

        return errors

    def _static_analysis(self, source_code: str) -> tuple[list[str], list[str], int]:
        """Perform static analysis on the source code."""
        errors = []
        warnings = []
        security_score = 100

        # Check for required patterns
        for pattern in self.required_patterns:
            if not re.search(pattern, source_code):
                errors.append(f"Missing required pattern: {pattern}")

        # Check for suspicious patterns
        suspicious_patterns = [
            (r"document\.cookie", "Accessing cookies"),
            (r"localStorage", "Accessing localStorage"),
            (r"sessionStorage", "Accessing sessionStorage"),
            (r"window\.\w+\s*=", "Modifying global window object"),
            (r"prototype\.\w+\s*=", "Modifying prototypes"),
            (r"__proto__", "Accessing __proto__"),
        ]

        for pattern, description in suspicious_patterns:
            if re.search(pattern, source_code):
                warnings.append(f"Suspicious pattern: {description}")
                security_score -= 10

        # Check code complexity
        lines = source_code.split("\n")
        if len(lines) > 1000:
            warnings.append("Module is very large (>1000 lines)")
            security_score -= 5

        return errors, warnings, security_score

    def _validate_api_usage(self, source_code: str) -> tuple[list[str], int]:
        """Validate API usage against allowlist/blocklist."""
        errors = []
        security_score = 100

        # Check for blocked APIs
        for blocked_api in self.blocked_apis:
            if re.search(rf"\b{re.escape(blocked_api)}\b", source_code):
                errors.append(f"Blocked API usage: {blocked_api}")
                security_score -= 20

        # Check for suspicious network calls
        network_patterns = [
            r'fetch\s*\(\s*[\'"`][^\'"`]*(?:javascript:|data:|file:)',
            r"new\s+Image\s*\(\s*\)\s*\.\s*src\s*=",
            r"new\s+XMLHttpRequest",
        ]

        for pattern in network_patterns:
            if re.search(pattern, source_code):
                errors.append("Suspicious network activity detected")
                security_score -= 15

        return errors, security_score

    def _check_security_patterns(self, source_code: str) -> tuple[list[str], int]:
        """Check for security-related patterns."""
        errors = []
        security_score = 100

        # Check for code injection attempts
        injection_patterns = [
            r"eval\s*\(",
            r"Function\s*\(",
            r'setTimeout\s*\(\s*[\'"`]',
            r'setInterval\s*\(\s*[\'"`]',
            r"document\.write\s*\(",
            r"\.innerHTML\s*=.*\+",  # Dynamic HTML construction
        ]

        for pattern in injection_patterns:
            if re.search(pattern, source_code):
                errors.append(f"Code injection risk detected: {pattern}")
                security_score -= 25

        return errors, security_score

    async def _validate_syntax(self, source_code: str) -> list[str]:
        """Validate JavaScript syntax using Node.js."""
        errors = []

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(source_code)
                temp_file = f.name

            # Check syntax with Node.js
            result = subprocess.run(["node", "--check", temp_file], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                errors.append(f"Syntax error: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            errors.append("Syntax validation timed out")
        except FileNotFoundError:
            # Node.js not available - skip syntax check
            pass
        except Exception as e:
            errors.append(f"Syntax validation failed: {e!s}")
        finally:
            # Cleanup
            try:
                Path(temp_file).unlink()
            except Exception:
                pass

        return errors

    async def _create_validated_module(self, manifest: ComponentManifest, source_code: str) -> str:
        """Create a validated ES6 module file."""
        # Create secure module wrapper
        wrapped_code = f"""
// Validated component module for {manifest.id}
// Generated on: {__import__("datetime").datetime.now().isoformat()}
// Security score: Module passed validation

// Module isolation wrapper
(function() {{
    'use strict';

    // Disable dangerous globals
    const eval = undefined;
    const Function = undefined;

    // Module code
    {source_code}

    // Export validation
    if (typeof {manifest.tag_name.replace("-", "").title()}Module === 'undefined') {{
        throw new Error('Module class not found');
    }}
}})();
"""

        # Create validated modules directory
        modules_dir = Path("validated_modules")
        modules_dir.mkdir(exist_ok=True)

        # Generate hash-based filename
        module_hash = hashlib.sha256(wrapped_code.encode()).hexdigest()[:16]
        module_file = modules_dir / f"{manifest.id}_{module_hash}.js"

        # Write validated module
        async with aiofiles.open(module_file, "w") as f:
            await f.write(wrapped_code)

        return str(module_file)


class ComponentValidationView(web.View):
    """API endpoint for component validation."""

    def __init__(self, request):
        super().__init__(request)
        self.validator = ComponentValidator()

    async def post(self) -> web.Response:
        """Validate a component submission."""
        try:
            data = await self.request.json()

            # Parse manifest
            manifest = ComponentManifest(**data["manifest"])
            source_code = data["source_code"]

            # Validate component
            result = await self.validator.validate_component(manifest, source_code)

            return web.json_response(
                {
                    "valid": result.valid,
                    "errors": result.errors,
                    "warnings": result.warnings,
                    "security_score": result.security_score,
                    "validated_module_url": f"/validated_modules/{Path(result.validated_module_path).name}"
                    if result.validated_module_path
                    else None,
                }
            )

        except Exception as e:
            return web.json_response(
                {"valid": False, "errors": [f"Validation request failed: {e!s}"], "warnings": [], "security_score": 0},
                status=400,
            )
