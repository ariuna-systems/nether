/**
 * Settings Web Component - Modern ES6 Implementation
 * Provides application settings management interface
 */

import './settings-component.css';

class SettingsWebComponent extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.settings = {};
        this.isDirty = false;

        // Bind methods
        this.loadSettings = this.loadSettings.bind(this);
        this.saveSettings = this.saveSettings.bind(this);
        this.handleInputChange = this.handleInputChange.bind(this);
    }

    connectedCallback() {
        this.render();
        this.loadSettings();
        this.attachEventListeners();
    }

    disconnectedCallback() {
        this.removeEventListeners();
    }

    static get observedAttributes() {
        return ['api-endpoint', 'theme'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            this.render();
        }
    }

    get apiEndpoint() {
        return this.getAttribute('api-endpoint') || '/api/settings';
    }

    get theme() {
        return this.getAttribute('theme') || 'light';
    }

    async loadSettings() {
        try {
            const response = await fetch(this.apiEndpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.settings = await response.json();
            this.isDirty = false;
            this.render();
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showError('Failed to load settings. Please try again.');
        }
    }

    async saveSettings() {
        if (!this.isDirty) return;

        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ settings: this.settings })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.isDirty = false;
            this.showSuccess('Settings saved successfully!');

            // Dispatch custom event
            this.dispatchEvent(new CustomEvent('settings-saved', {
                detail: { settings: this.settings },
                bubbles: true
            }));
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showError('Failed to save settings. Please try again.');
        }
    }

    updateSetting(path, value) {
        const keys = path.split('.');
        let current = this.settings;

        // Navigate to the parent object
        for (let i = 0; i < keys.length - 1; i++) {
            if (!current[keys[i]]) {
                current[keys[i]] = {};
            }
            current = current[keys[i]];
        }

        // Set the value
        current[keys[keys.length - 1]] = value;
        this.isDirty = true;

        // Update save button state
        this.updateSaveButton();
    }

    handleInputChange(event) {
        const { name, value, type, checked } = event.target;
        const actualValue = type === 'checkbox' ? checked :
                           type === 'number' ? Number(value) : value;

        this.updateSetting(name, actualValue);
    }

    updateSaveButton() {
        const saveBtn = this.shadowRoot.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.disabled = !this.isDirty;
            saveBtn.textContent = this.isDirty ? 'Save Changes' : 'Saved';
        }
    }

    attachEventListeners() {
        const form = this.shadowRoot.querySelector('.settings-form');
        if (form) {
            form.addEventListener('change', this.handleInputChange);
            form.addEventListener('input', this.handleInputChange);
        }

        const saveBtn = this.shadowRoot.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', this.saveSettings);
        }
    }

    removeEventListeners() {
        const form = this.shadowRoot.querySelector('.settings-form');
        if (form) {
            form.removeEventListener('change', this.handleInputChange);
            form.removeEventListener('input', this.handleInputChange);
        }

        const saveBtn = this.shadowRoot.querySelector('.save-btn');
        if (saveBtn) {
            saveBtn.removeEventListener('click', this.saveSettings);
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        const notification = this.shadowRoot.querySelector('.notification');
        if (notification) {
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.style.display = 'block';

            setTimeout(() => {
                notification.style.display = 'none';
            }, 3000);
        }
    }

    render() {
        if (!this.settings.general) {
            this.shadowRoot.innerHTML = this.getLoadingTemplate();
            return;
        }

        this.shadowRoot.innerHTML = this.getTemplate();
        this.updateSaveButton();
    }

    getLoadingTemplate() {
        return `
            <style>${this.getStyles()}</style>
            <div class="loading">
                <div class="spinner"></div>
                <p>Loading settings...</p>
            </div>
        `;
    }

    getTemplate() {
        return `
            <style>${this.getStyles()}</style>
            <div class="settings-container">
                <header class="settings-header">
                    <h1>Application Settings</h1>
                    <p>Configure your application preferences and system settings</p>
                </header>

                <div class="notification" style="display: none;"></div>

                <form class="settings-form">
                    ${this.getGeneralSettingsSection()}
                    ${this.getSecuritySettingsSection()}
                    ${this.getNotificationSettingsSection()}
                </form>

                <div class="settings-actions">
                    <button type="button" class="save-btn" ${!this.isDirty ? 'disabled' : ''}>
                        ${this.isDirty ? 'Save Changes' : 'Saved'}
                    </button>
                </div>
            </div>
        `;
    }

    getGeneralSettingsSection() {
        const { general } = this.settings;
        return `
            <section class="settings-section">
                <h2>General Settings</h2>
                <div class="setting-group">
                    <label class="setting-label">
                        Application Name
                        <input type="text" name="general.app_name"
                               value="${general.app_name}"
                               class="setting-input">
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        Description
                        <textarea name="general.app_description"
                                  class="setting-input"
                                  rows="3">${general.app_description}</textarea>
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        Theme
                        <select name="general.theme" class="setting-input">
                            <option value="light" ${general.theme === 'light' ? 'selected' : ''}>Light</option>
                            <option value="dark" ${general.theme === 'dark' ? 'selected' : ''}>Dark</option>
                            <option value="auto" ${general.theme === 'auto' ? 'selected' : ''}>Auto</option>
                        </select>
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-label">
                        Timezone
                        <select name="general.timezone" class="setting-input">
                            <option value="UTC" ${general.timezone === 'UTC' ? 'selected' : ''}>UTC</option>
                            <option value="EST" ${general.timezone === 'EST' ? 'selected' : ''}>EST</option>
                            <option value="PST" ${general.timezone === 'PST' ? 'selected' : ''}>PST</option>
                        </select>
                    </label>
                </div>
            </section>
        `;
    }

    getSecuritySettingsSection() {
        const { security } = this.settings;
        return `
            <section class="settings-section">
                <h2>Security Settings</h2>
                <div class="setting-group">
                    <label class="setting-label">
                        Session Timeout (minutes)
                        <input type="number" name="security.session_timeout"
                               value="${security.session_timeout}"
                               class="setting-input" min="5" max="480">
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-checkbox">
                        <input type="checkbox" name="security.two_factor_auth"
                               ${security.two_factor_auth ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        Enable Two-Factor Authentication
                    </label>
                </div>
            </section>
        `;
    }

    getNotificationSettingsSection() {
        const { notifications } = this.settings;
        return `
            <section class="settings-section">
                <h2>Notification Settings</h2>
                <div class="setting-group">
                    <label class="setting-checkbox">
                        <input type="checkbox" name="notifications.email_notifications"
                               ${notifications.email_notifications ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        Enable Email Notifications
                    </label>
                </div>
                <div class="setting-group">
                    <label class="setting-checkbox">
                        <input type="checkbox" name="notifications.push_notifications"
                               ${notifications.push_notifications ? 'checked' : ''}>
                        <span class="checkmark"></span>
                        Enable Push Notifications
                    </label>
                </div>
            </section>
        `;
    }

    getStyles() {
        return `
            :host {
                display: block;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                color: var(--text-color, #333);
                background: var(--bg-color, #f8f9fa);
                border-radius: 8px;
                overflow: hidden;
            }

            .settings-container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }

            .settings-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }

            .settings-header h1 {
                margin: 0 0 0.5rem 0;
                font-size: 2rem;
                font-weight: 600;
            }

            .settings-header p {
                margin: 0;
                opacity: 0.9;
                font-size: 1.1rem;
            }

            .notification {
                margin: 1rem;
                padding: 1rem;
                border-radius: 6px;
                font-weight: 500;
            }

            .notification.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }

            .notification.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }

            .settings-form {
                padding: 2rem;
            }

            .settings-section {
                margin-bottom: 2rem;
                padding-bottom: 2rem;
                border-bottom: 1px solid #e9ecef;
            }

            .settings-section:last-child {
                border-bottom: none;
                margin-bottom: 0;
            }

            .settings-section h2 {
                margin: 0 0 1.5rem 0;
                color: #495057;
                font-size: 1.3rem;
                font-weight: 600;
            }

            .setting-group {
                margin-bottom: 1.5rem;
            }

            .setting-label {
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 500;
                color: #555;
            }

            .setting-input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 1rem;
                transition: border-color 0.2s ease;
                box-sizing: border-box;
            }

            .setting-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }

            .setting-checkbox {
                display: flex;
                align-items: center;
                cursor: pointer;
                font-weight: 500;
                color: #555;
            }

            .setting-checkbox input[type="checkbox"] {
                margin-right: 0.75rem;
                width: 18px;
                height: 18px;
                cursor: pointer;
            }

            .settings-actions {
                padding: 1.5rem 2rem;
                background: #f8f9fa;
                border-top: 1px solid #e9ecef;
                text-align: right;
            }

            .save-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 0.75rem 2rem;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .save-btn:hover:not(:disabled) {
                background: #5a6fd8;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }

            .save-btn:disabled {
                background: #6c757d;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            .loading {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 4rem 2rem;
                text-align: center;
            }

            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #e9ecef;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 1rem;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Dark theme support */
            :host([theme="dark"]) {
                --text-color: #f8f9fa;
                --bg-color: #343a40;
            }

            @media (max-width: 768px) {
                .settings-container {
                    margin: 0;
                    border-radius: 0;
                }

                .settings-header {
                    padding: 1.5rem;
                }

                .settings-form {
                    padding: 1.5rem;
                }

                .settings-actions {
                    padding: 1rem 1.5rem;
                }
            }
        `;
    }
}

// Export and register the component
export default SettingsWebComponent;

if (!customElements.get('settings-component')) {
    customElements.define('settings-component', SettingsWebComponent);
}
