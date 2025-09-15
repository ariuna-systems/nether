"""
Secure Module Registry for managing validated web components.
"""

import hashlib
import json
from pathlib import Path

import aiofiles
from aiohttp import web

from .validator import ComponentManifest, ComponentValidator, ValidationResult


class SecureComponentRegistry:
    """Registry for securely managing external web components."""

    def __init__(self, components_dir: str = "components", validated_dir: str = "validated_modules"):
        self.components_dir = Path(components_dir)
        self.validated_dir = Path(validated_dir)
        self.validator = ComponentValidator()
        self.registered_components: dict[str, ComponentManifest] = {}
        self.validation_cache: dict[str, ValidationResult] = {}

        # Ensure directories exist
        self.components_dir.mkdir(exist_ok=True)
        self.validated_dir.mkdir(exist_ok=True)

    async def register_component(self, manifest: ComponentManifest, source_code: str) -> ValidationResult:
        """Register a new component after validation."""
        # Generate component hash for caching
        component_hash = hashlib.sha256(f"{manifest.id}:{manifest.version}:{source_code}".encode()).hexdigest()

        # Check cache first
        if component_hash in self.validation_cache:
            cached_result = self.validation_cache[component_hash]
            if cached_result.valid:
                self.registered_components[manifest.id] = manifest
            return cached_result

        # Validate component
        result = await self.validator.validate_component(manifest, source_code)

        # Cache result
        self.validation_cache[component_hash] = result

        # Register if valid
        if result.valid:
            self.registered_components[manifest.id] = manifest
            await self._save_component_manifest(manifest)
            print(f"✅ Module {manifest.id} registered successfully")
        else:
            print(f"❌ Module {manifest.id} failed validation:")
            for error in result.errors:
                print(f"   - {error}")

        return result

    async def get_component_manifest(self, component_id: str) -> ComponentManifest | None:
        """Get manifest for a registered component."""
        return self.registered_components.get(component_id)

    async def list_components(self) -> list[ComponentManifest]:
        """List all registered components."""
        return list(self.registered_components.values())

    async def unregister_component(self, component_id: str) -> bool:
        """Unregister a component."""
        if component_id in self.registered_components:
            del self.registered_components[component_id]

            # Remove manifest file
            manifest_file = self.components_dir / f"{component_id}.json"
            if manifest_file.exists():
                manifest_file.unlink()

            print(f"✅ Module {component_id} unregistered")
            return True

        return False

    async def get_validated_module_url(self, component_id: str) -> str | None:
        """Get the URL for a validated component module."""
        if component_id not in self.registered_components:
            return None

        manifest = self.registered_components[component_id]
        # Construct validated module URL
        return f"/validated_modules/{component_id}_{manifest.version}.js"

    async def _save_component_manifest(self, manifest: ComponentManifest) -> None:
        """Save component manifest to disk."""
        manifest_file = self.components_dir / f"{manifest.id}.json"
        manifest_data = {
            "id": manifest.id,
            "name": manifest.name,
            "version": manifest.version,
            "author": manifest.author,
            "description": manifest.description,
            "tag_name": manifest.tag_name,
            "module_url": manifest.module_url,
            "permissions": manifest.permissions,
            "api_endpoints": manifest.api_endpoints,
            "signature": manifest.signature,
            "hash": manifest.hash,
        }

        async with aiofiles.open(manifest_file, "w") as f:
            await f.write(json.dumps(manifest_data, indent=2))

    async def load_components_from_disk(self) -> None:
        """Load previously registered components from disk."""
        for manifest_file in self.components_dir.glob("*.json"):
            try:
                async with aiofiles.open(manifest_file, "r") as f:
                    manifest_data = json.loads(await f.read())

                manifest = ComponentManifest(**manifest_data)
                self.registered_components[manifest.id] = manifest
                print(f"📦 Loaded component {manifest.id} from disk")

            except Exception as e:
                print(f"❌ Failed to load component from {manifest_file}: {e}")


class ComponentRegistryView(web.View):
    """API endpoints for component registry management."""

    def __init__(self, request):
        super().__init__(request)
        self.registry: SecureComponentRegistry = request.app["component_registry"]

    async def get(self) -> web.Response:
        """List all registered components."""
        components = await self.registry.list_components()
        return web.json_response(
            [
                {
                    "id": comp.id,
                    "name": comp.name,
                    "version": comp.version,
                    "author": comp.author,
                    "description": comp.description,
                    "tag_name": comp.tag_name,
                    "permissions": comp.permissions,
                    "validated_module_url": await self.registry.get_validated_module_url(comp.id),
                }
                for comp in components
            ]
        )

    async def post(self) -> web.Response:
        """Register a new component."""
        try:
            data = await self.request.json()

            # Parse manifest
            manifest = ComponentManifest(**data["manifest"])
            source_code = data["source_code"]

            # Register component
            result = await self.registry.register_component(manifest, source_code)

            if result.valid:
                return web.json_response(
                    {
                        "success": True,
                        "message": f"Module {manifest.id} registered successfully",
                        "component_id": manifest.id,
                        "validated_module_url": await self.registry.get_validated_module_url(manifest.id),
                        "security_score": result.security_score,
                        "warnings": result.warnings,
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": False,
                        "message": "Module validation failed",
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "security_score": result.security_score,
                    },
                    status=400,
                )

        except Exception as e:
            return web.json_response(
                {
                    "success": False,
                    "message": f"Registration failed: {e!s}",
                    "errors": [f"Request processing error: {e!s}"],
                },
                status=500,
            )

    async def delete(self) -> web.Response:
        """Unregister a component."""
        try:
            component_id = self.request.match_info.get("component_id")
            if not component_id:
                return web.json_response({"success": False, "message": "Module ID required"}, status=400)

            success = await self.registry.unregister_component(component_id)

            if success:
                return web.json_response(
                    {"success": True, "message": f"Module {component_id} unregistered successfully"}
                )
            else:
                return web.json_response({"success": False, "message": f"Module {component_id} not found"}, status=404)

        except Exception as e:
            return web.json_response({"success": False, "message": f"Unregistration failed: {e!s}"}, status=500)


class ValidatedModuleView(web.View):
    """Serve validated component modules."""

    async def get(self) -> web.Response:
        """Serve a validated component module."""
        try:
            module_name = self.request.match_info.get("module_name")
            if not module_name:
                return web.Response(status=404)

            # Security check - ensure only validated modules are served
            validated_dir = Path("validated_modules")
            module_file = validated_dir / module_name

            # Ensure file exists and is within validated directory
            if not module_file.exists() or not module_file.is_relative_to(validated_dir):
                return web.Response(status=404)

            # Serve the validated module
            async with aiofiles.open(module_file, "r") as f:
                content = await f.read()

            return web.Response(
                text=content,
                content_type="application/javascript",
                headers={"Content-Security-Policy": "default-src 'self'", "X-Content-Type-Options": "nosniff"},
            )

        except Exception:
            return web.Response(status=500)
