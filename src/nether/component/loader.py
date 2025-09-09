"""
Secure Component Loader - Frontend JavaScript for safe component loading.
"""

from aiohttp import web


class SecureComponentLoaderView(web.View):
    """Serve the secure component loader JavaScript."""

    async def get(self) -> web.Response:
        """Return the secure component loader script."""
        javascript_code = '''
class SecureComponentLoader {
    constructor() {
        this.loadedComponents = new Set();
        this.componentCache = new Map();
        this.securityHeaders = {
            'Content-Security-Policy': "default-src 'self'",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        };

        console.log('️ Secure Component Loader initialized');
    }

    /**
     * Load a validated component module securely
     * @param {string} componentId - The component ID
     * @param {Object} manifest - Component manifest
     * @returns {Promise<boolean>} - Success status
     */
    async loadComponent(componentId, manifest) {
        try {
            // Prevent duplicate loading
            if (this.loadedComponents.has(componentId)) {
                console.log(`️ Component ${componentId} already loaded`);
                return true;
            }

            console.log(` Loading secure component: ${componentId}`);

            // 1. Validate manifest
            if (!this.validateManifest(manifest)) {
                throw new Error(`Invalid manifest for component ${componentId}`);
            }

            // 2. Check if component is registered on server
            const registrationCheck = await this.verifyComponentRegistration(componentId);
            if (!registrationCheck.valid) {
                throw new Error(`Component ${componentId} not registered or validation failed`);
            }

            // 3. Load the validated module
            const moduleUrl = registrationCheck.validated_module_url;
            if (!moduleUrl) {
                throw new Error(`No validated module URL for component ${componentId}`);
            }

            // 4. Import as ES6 module (secure)
            const module = await this.secureModuleImport(moduleUrl);

            // 5. Final validation and registration
            if (this.validateComponentClass(module, manifest)) {
                // Register the custom element
                if (!customElements.get(manifest.tag_name)) {
                    customElements.define(manifest.tag_name, module.default || module[manifest.class_name]);
                    console.log(` Component ${componentId} registered as <${manifest.tag_name}>`);
                }

                this.loadedComponents.add(componentId);
                this.componentCache.set(componentId, {
                    manifest,
                    module,
                    loadedAt: Date.now()
                });

                return true;
            } else {
                throw new Error(`Component class validation failed for ${componentId}`);
            }

        } catch (error) {
            console.error(` Failed to load component ${componentId}:`, error);
            return false;
        }
    }

    /**
     * Validate component manifest
     * @param {Object} manifest - Component manifest
     * @returns {boolean} - Validation result
     */
    validateManifest(manifest) {
        const required = ['id', 'name', 'version', 'tag_name', 'author'];
        for (const field of required) {
            if (!manifest[field]) {
                console.error(` Missing required field: ${field}`);
                return false;
            }
        }

        // Tag name validation (kebab-case)
        if (!/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/.test(manifest.tag_name)) {
            console.error(` Invalid tag name: ${manifest.tag_name}`);
            return false;
        }

        // Version validation (semantic versioning)
        if (!/^\\d+\\.\\d+\\.\\d+$/.test(manifest.version)) {
            console.error(` Invalid version format: ${manifest.version}`);
            return false;
        }

        return true;
    }

    /**
     * Verify component registration with server
     * @param {string} componentId - Component ID
     * @returns {Promise<Object>} - Registration status
     */
    async verifyComponentRegistration(componentId) {
        try {
            const response = await fetch(`/api/components/registry/${componentId}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                return { valid: false, error: `HTTP ${response.status}` };
            }

            return await response.json();

        } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    /**
     * Securely import a validated module
     * @param {string} moduleUrl - URL to the validated module
     * @returns {Promise<Object>} - Imported module
     */
    async secureModuleImport(moduleUrl) {
        try {
            // Validate URL to prevent injection
            const url = new URL(moduleUrl, window.location.origin);
            if (url.origin !== window.location.origin) {
                throw new Error('Cross-origin module loading not allowed');
            }

            if (!url.pathname.startsWith('/validated_modules/')) {
                throw new Error('Only validated modules can be loaded');
            }

            // Import the module
            const module = await import(url.href);

            if (!module) {
                throw new Error('Module import returned null/undefined');
            }

            return module;

        } catch (error) {
            throw new Error(`Module import failed: ${error.message}`);
        }
    }

    /**
     * Validate the imported component class
     * @param {Object} module - Imported module
     * @param {Object} manifest - Component manifest
     * @returns {boolean} - Validation result
     */
    validateComponentClass(module, manifest) {
        try {
            // Get the component class
            const ComponentClass = module.default || module[manifest.class_name];

            if (!ComponentClass) {
                console.error(' Component class not found in module');
                return false;
            }

            // Check inheritance
            if (!(ComponentClass.prototype instanceof HTMLElement)) {
                console.error(' Component must extend HTMLElement');
                return false;
            }

            // Check for required lifecycle methods
            const requiredMethods = ['connectedCallback'];
            for (const method of requiredMethods) {
                if (typeof ComponentClass.prototype[method] !== 'function') {
                    console.error(` Missing required method: ${method}`);
                    return false;
                }
            }

            return true;

        } catch (error) {
            console.error(' Component class validation error:', error);
            return false;
        }
    }

    /**
     * Create a component instance safely
     * @param {string} componentId - Component ID
     * @param {Object} attributes - Element attributes
     * @returns {HTMLElement|null} - Component instance
     */
    createComponent(componentId, attributes = {}) {
        try {
            const cached = this.componentCache.get(componentId);
            if (!cached) {
                console.error(` Component ${componentId} not loaded`);
                return null;
            }

            const element = document.createElement(cached.manifest.tag_name);

            // Set attributes safely
            for (const [key, value] of Object.entries(attributes)) {
                if (typeof key === 'string' && key.match(/^[a-zA-Z][a-zA-Z0-9-]*$/)) {
                    element.setAttribute(key, String(value));
                }
            }

            return element;

        } catch (error) {
            console.error(` Failed to create component ${componentId}:`, error);
            return null;
        }
    }

    /**
     * List all loaded components
     * @returns {Array} - List of loaded component IDs
     */
    getLoadedComponents() {
        return Array.from(this.loadedComponents);
    }

    /**
     * Unload a component (remove from registry)
     * @param {string} componentId - Component ID
     * @returns {boolean} - Success status
     */
    unloadComponent(componentId) {
        try {
            if (!this.loadedComponents.has(componentId)) {
                return false;
            }

            const cached = this.componentCache.get(componentId);
            if (cached && cached.manifest.tag_name) {
                // Note: CustomElements cannot be unregistered,
                // so we just remove from our tracking
                this.loadedComponents.delete(componentId);
                this.componentCache.delete(componentId);

                console.log(` Component ${componentId} unloaded from registry`);
                return true;
            }

            return false;

        } catch (error) {
            console.error(` Failed to unload component ${componentId}:`, error);
            return false;
        }
    }

    /**
     * Get component info
     * @param {string} componentId - Component ID
     * @returns {Object|null} - Component information
     */
    getComponentInfo(componentId) {
        const cached = this.componentCache.get(componentId);
        if (!cached) {
            return null;
        }

        return {
            id: componentId,
            manifest: { ...cached.manifest },
            loadedAt: cached.loadedAt,
            tagName: cached.manifest.tag_name
        };
    }
}

// Create global instance
if (!window.secureComponentLoader) {
    window.secureComponentLoader = new SecureComponentLoader();
    console.log('️ Secure Component Loader ready');

    // Add helper function to global scope
    window.loadSecureComponent = async (componentId, manifest) => {
        return await window.secureComponentLoader.loadComponent(componentId, manifest);
    };

    window.createSecureComponent = (componentId, attributes) => {
        return window.secureComponentLoader.createComponent(componentId, attributes);
    };
}

// Export for module usage
export default window.secureComponentLoader;
'''

        return web.Response(
            text=javascript_code,
            content_type='application/javascript',
            headers={
                'Content-Security-Policy': "default-src 'self'",
                'X-Content-Type-Options': 'nosniff'
            }
        )
