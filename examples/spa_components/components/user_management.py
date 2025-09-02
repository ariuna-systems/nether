"""
User Management Component - User account and role management.
"""

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web

from nether.component import Component
from nether.message import Command, Event, Message
from nether.server import RegisterView


@dataclass(frozen=True, kw_only=True, slots=True)
class GetUsers(Command):
    """Command to get users list."""

    ...


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateUser(Command):
    """Command to create a new user."""

    username: str
    email: str
    role: str


@dataclass(frozen=True, kw_only=True, slots=True)
class UserCreated(Event):
    """Event when user is created."""

    user_id: str
    username: str


class UserManagementAPIView(web.View):
    """API endpoints for user management operations."""

    async def get(self) -> web.Response:
        """Get users list."""
        # Comprehensive mock users data
        users = [
            {
                "id": "1",
                "username": "john.doe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "role": "admin",
                "status": "active",
                "last_login": "2 hours ago",
                "created_at": "2024-01-15",
                "profile_image": "👨‍💼",
                "permissions": ["read", "write", "admin", "delete"],
                "department": "IT",
                "login_count": 347,
                "last_activity": "Viewed dashboard",
                "location": "New York, USA",
                "two_factor_enabled": True,
                "account_locked": False
            },
            {
                "id": "2", 
                "username": "jane.smith",
                "email": "jane.smith@example.com",
                "full_name": "Jane Smith",
                "role": "manager",
                "status": "active",
                "last_login": "1 day ago",
                "created_at": "2024-02-10",
                "profile_image": "👩‍💼",
                "permissions": ["read", "write", "manage_team"],
                "department": "Marketing",
                "login_count": 189,
                "last_activity": "Updated campaign",
                "location": "London, UK",
                "two_factor_enabled": True,
                "account_locked": False
            },
            {
                "id": "3",
                "username": "mike.wilson",
                "email": "mike.wilson@example.com", 
                "full_name": "Mike Wilson",
                "role": "user",
                "status": "inactive",
                "last_login": "1 week ago",
                "created_at": "2024-01-20",
                "profile_image": "👨‍💻",
                "permissions": ["read"],
                "department": "Development",
                "login_count": 78,
                "last_activity": "Code review",
                "location": "San Francisco, USA",
                "two_factor_enabled": False,
                "account_locked": False
            },
            {
                "id": "4",
                "username": "sarah.johnson", 
                "email": "sarah.johnson@example.com",
                "full_name": "Sarah Johnson",
                "role": "user",
                "status": "active",
                "last_login": "3 hours ago",
                "created_at": "2024-03-05",
                "profile_image": "👩‍🔬",
                "permissions": ["read", "write"],
                "department": "Research",
                "login_count": 156,
                "last_activity": "Generated report",
                "location": "Toronto, Canada", 
                "two_factor_enabled": True,
                "account_locked": False
            },
            {
                "id": "5",
                "username": "alex.chen",
                "email": "alex.chen@example.com",
                "full_name": "Alex Chen",
                "role": "user", 
                "status": "pending",
                "last_login": "Never",
                "created_at": "2024-03-20",
                "profile_image": "👨‍🎨",
                "permissions": ["read"],
                "department": "Design",
                "login_count": 0,
                "last_activity": "Account created", 
                "location": "Sydney, Australia",
                "two_factor_enabled": False,
                "account_locked": False
            },
            {
                "id": "6",
                "username": "lisa.martinez",
                "email": "lisa.martinez@example.com",
                "full_name": "Lisa Martinez",
                "role": "moderator",
                "status": "suspended",
                "last_login": "2 weeks ago", 
                "created_at": "2023-11-12",
                "profile_image": "👩‍⚖️",
                "permissions": ["read", "moderate"],
                "department": "Legal",
                "login_count": 245,
                "last_activity": "Policy violation",
                "location": "Madrid, Spain",
                "two_factor_enabled": True,
                "account_locked": True
            }
        ]

        # User statistics
        stats = {
            "total_users": len(users),
            "active_users": len([u for u in users if u["status"] == "active"]),
            "inactive_users": len([u for u in users if u["status"] == "inactive"]),
            "pending_users": len([u for u in users if u["status"] == "pending"]), 
            "suspended_users": len([u for u in users if u["status"] == "suspended"]),
            "admin_users": len([u for u in users if u["role"] == "admin"]),
            "manager_users": len([u for u in users if u["role"] == "manager"]),
            "regular_users": len([u for u in users if u["role"] == "user"]),
            "new_this_month": len([u for u in users if u["created_at"].startswith("2024-03")]),
            "two_factor_enabled": len([u for u in users if u["two_factor_enabled"]]),
            "departments": list(set([u["department"] for u in users])),
            "recent_activity": [
                {"user": "john.doe", "action": "Updated user permissions", "time": "15 min ago"},
                {"user": "jane.smith", "action": "Deactivated user account", "time": "1 hour ago"},
                {"user": "sarah.johnson", "action": "Bulk user import", "time": "2 hours ago"},
                {"user": "john.doe", "action": "Password policy updated", "time": "4 hours ago"},
                {"user": "mike.wilson", "action": "Role assignment changed", "time": "6 hours ago"}
            ]
        }

        return web.json_response({"users": users, "stats": stats})

    async def post(self) -> web.Response:
        """Create a new user."""
        data = await self.request.json()

        # Mock user creation
        new_user = {
            "id": str(int(time.time())),
            "username": data.get("username"),
            "email": data.get("email"),
            "role": data.get("role", "user"),
            "status": "active",
            "created_at": time.strftime("%Y-%m-%d"),
            "last_login": "Never",
        }

        return web.json_response(new_user, status=201)


class UserManagementComponentView(web.View):
    """Serve the user management web component HTML."""

    async def get(self) -> web.Response:
        """Return user management component HTML."""
        html = """
<div class="component-header">
    <h1 class="component-title">👥 User Management</h1>
    <p class="component-description">Manage user accounts, roles, and permissions</p>
</div>

<style>
    .users-container {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
    }
    .users-main {
        flex: 1;
    }
    .users-sidebar {
        width: 250px;
    }

    .user-stats {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .stat-item {
        display: flex;
        justify-content: space-between;
        margin: 10px 0;
        padding: 8px 0;
        border-bottom: 1px solid #f1f1f1;
    }
    .stat-item:last-child {
        border-bottom: none;
    }
    .stat-value {
        font-weight: bold;
        color: #3498db;
    }

    .create-user-form {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .form-group {
        margin-bottom: 15px;
    }
    .form-label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
        color: #2c3e50;
    }
    .form-input, .form-select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-size: 14px;
    }
    .btn-primary {
        background: #3498db;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    }
    .btn-primary:hover {
        background: #2980b9;
    }

    .users-table {
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .table-header {
        background: #f8f9fa;
        padding: 15px 20px;
        border-bottom: 1px solid #dee2e6;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .table {
        width: 100%;
        border-collapse: collapse;
    }
    .table th, .table td {
        padding: 12px 15px;
        text-align: left;
        border-bottom: 1px solid #f1f1f1;
    }
    .table th {
        background: #f8f9fa;
        font-weight: bold;
        color: #2c3e50;
    }
    .table tr:hover {
        background: #f8f9fa;
    }

    .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .status-active {
        background: #d4edda;
        color: #155724;
    }
    .status-inactive {
        background: #f8d7da;
        color: #721c24;
    }

    .role-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: bold;
    }
    .role-admin {
        background: #e7f3ff;
        color: #0066cc;
    }
    .role-user {
        background: #f0f0f0;
        color: #666;
    }
    .role-moderator {
        background: #fff3e0;
        color: #e65100;
    }

    .loading {
        text-align: center;
        padding: 40px;
        color: #7f8c8d;
    }
</style>

<div id="users-content">
    <div class="loading">Loading user data...</div>
</div>

<script>
    class UserManagementComponent {
        constructor() {
            this.data = null;
            this.init();
        }

        async init() {
            await this.loadData();
            this.render();

            // Listen for component loaded event
            window.addEventListener('component-user_management-loaded', (event) => {
                this.data = event.detail.data;
                this.render();
            });
        }

        async loadData() {
            try {
                const response = await fetch('/api/users/data');
                this.data = await response.json();
            } catch (error) {
                console.error('Failed to load user data:', error);
                this.data = { error: 'Failed to load data' };
            }
        }

        async createUser(userData) {
            try {
                const response = await fetch('/api/users/data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });

                if (response.ok) {
                    await this.loadData();
                    this.render();
                    // Clear form
                    document.getElementById('create-user-form').reset();
                }
            } catch (error) {
                console.error('Failed to create user:', error);
            }
        }

        render() {
            const container = document.getElementById('users-content');
            if (!this.data) return;

            if (this.data.error) {
                container.innerHTML = `<div class="error">Error: ${this.data.error}</div>`;
                return;
            }

            container.innerHTML = `
                <div class="users-container">
                    <div class="users-main">
                        <!-- User Statistics Overview -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px;">
                            <div class="metric-card" style="border-left-color: #27ae60;">
                                <div class="metric-label">Total Users</div>
                                <div class="metric-value" style="color: #27ae60;">${this.data.stats.total_users}</div>
                            </div>
                            <div class="metric-card" style="border-left-color: #3498db;">
                                <div class="metric-label">Active Users</div>
                                <div class="metric-value" style="color: #3498db;">${this.data.stats.active_users}</div>
                            </div>
                            <div class="metric-card" style="border-left-color: #f39c12;">
                                <div class="metric-label">Pending</div>
                                <div class="metric-value" style="color: #f39c12;">${this.data.stats.pending_users}</div>
                            </div>
                            <div class="metric-card" style="border-left-color: #e74c3c;">
                                <div class="metric-label">Suspended</div>
                                <div class="metric-value" style="color: #e74c3c;">${this.data.stats.suspended_users}</div>
                            </div>
                        </div>

                        <div class="users-table">
                            <div class="table-header">
                                <span>👥 User Directory (${this.data.stats.total_users} users)</span>
                                <button class="btn-primary" onclick="userMgmt.toggleCreateForm()">+ Add User</button>
                            </div>

                            <div id="create-form" style="display: none; padding: 20px; background: #f8f9fa;">
                                <h4 style="margin-bottom: 15px;">➕ Create New User</h4>
                                <form id="create-user-form">
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                                        <div class="form-group">
                                            <label class="form-label">Username</label>
                                            <input type="text" name="username" class="form-input" required>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Full Name</label>
                                            <input type="text" name="full_name" class="form-input" required>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Email</label>
                                            <input type="email" name="email" class="form-input" required>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Department</label>
                                            <select name="department" class="form-select">
                                                ${this.data.stats.departments.map(dept => 
                                                    `<option value="${dept}">${dept}</option>`
                                                ).join('')}
                                            </select>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Role</label>
                                            <select name="role" class="form-select">
                                                <option value="user">User</option>
                                                <option value="moderator">Moderator</option>
                                                <option value="manager">Manager</option>
                                                <option value="admin">Admin</option>
                                            </select>
                                        </div>
                                        <div class="form-group">
                                            <label class="form-label">Location</label>
                                            <input type="text" name="location" class="form-input" placeholder="City, Country">
                                        </div>
                                    </div>
                                    <div style="margin-top: 15px;">
                                        <button type="submit" class="btn-primary">Create User</button>
                                        <button type="button" class="btn-secondary" onclick="userMgmt.toggleCreateForm()">Cancel</button>
                                    </div>
                                </form>
                            </div>

                            <!-- Enhanced User Table -->
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>User</th>
                                        <th>Role & Department</th>
                                        <th>Status</th>
                                        <th>Activity</th>
                                        <th>Location</th>
                                        <th>Security</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${this.data.users.map(user => `
                                        <tr>
                                            <td>
                                                <div style="display: flex; align-items: center; gap: 10px;">
                                                    <span style="font-size: 1.5em;">${user.profile_image}</span>
                                                    <div>
                                                        <strong>${user.full_name}</strong><br>
                                                        <small style="color: #666;">@${user.username}</small><br>
                                                        <small style="color: #666;">${user.email}</small>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                <span class="role-badge role-${user.role}">${user.role}</span><br>
                                                <small style="color: #666;">${user.department}</small>
                                            </td>
                                            <td>
                                                <span class="status-badge status-${user.status}">${user.status}</span>
                                                ${user.account_locked ? '<br><small style="color: #e74c3c;">🔒 Locked</small>' : ''}
                                            </td>
                                            <td>
                                                <strong>Last:</strong> ${user.last_login}<br>
                                                <small style="color: #666;">${user.last_activity}</small><br>
                                                <small style="color: #666;">Logins: ${user.login_count}</small>
                                            </td>
                                            <td>
                                                <small>${user.location}</small>
                                            </td>
                                            <td>
                                                ${user.two_factor_enabled ? 
                                                    '<span style="color: #27ae60;">🔐 2FA</span>' : 
                                                    '<span style="color: #f39c12;">⚠️ No 2FA</span>'
                                                }<br>
                                                <small>Permissions: ${user.permissions.length}</small>
                                            </td>
                                            <td>
                                                <button style="padding: 4px 8px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; background: #3498db; color: white;" 
                                                        onclick="userMgmt.editUser('${user.id}')">Edit</button><br>
                                                <button style="padding: 4px 8px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; background: #e74c3c; color: white;" 
                                                        onclick="userMgmt.toggleUserStatus('${user.id}')">
                                                    ${user.status === 'active' ? 'Suspend' : 'Activate'}
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="users-sidebar">
                        <!-- Enhanced Statistics -->
                        <div class="user-stats">
                            <h3>📊 User Statistics</h3>
                            <div class="stat-item">
                                <span>👥 Total Users</span>
                                <span class="stat-value">${this.data.stats.total_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>✅ Active</span>
                                <span class="stat-value" style="color: #27ae60;">${this.data.stats.active_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>⏸️ Inactive</span>
                                <span class="stat-value" style="color: #95a5a6;">${this.data.stats.inactive_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>⏳ Pending</span>
                                <span class="stat-value" style="color: #f39c12;">${this.data.stats.pending_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>🚫 Suspended</span>
                                <span class="stat-value" style="color: #e74c3c;">${this.data.stats.suspended_users}</span>
                            </div>
                            <hr style="margin: 15px 0;">
                            <div class="stat-item">
                                <span>👑 Admins</span>
                                <span class="stat-value">${this.data.stats.admin_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>🏢 Managers</span>
                                <span class="stat-value">${this.data.stats.manager_users}</span>
                            </div>
                            <div class="stat-item">
                                <span>👤 Regular Users</span>
                                <span class="stat-value">${this.data.stats.regular_users}</span>
                            </div>
                            <hr style="margin: 15px 0;">
                            <div class="stat-item">
                                <span>🔐 2FA Enabled</span>
                                <span class="stat-value">${this.data.stats.two_factor_enabled}</span>
                            </div>
                            <div class="stat-item">
                                <span>📅 New This Month</span>
                                <span class="stat-value">${this.data.stats.new_this_month}</span>
                            </div>
                        </div>

                        <!-- Recent Activity -->
                        <div class="user-stats" style="margin-top: 20px;">
                            <h3>📋 Recent Admin Activity</h3>
                            ${this.data.stats.recent_activity.map(activity => `
                                <div style="padding: 8px 0; border-bottom: 1px solid #eee;">
                                    <strong>${activity.user}</strong><br>
                                    <small style="color: #666;">${activity.action}</small><br>
                                    <small style="color: #999;">${activity.time}</small>
                                </div>
                            `).join('')}
                        </div>

                        <!-- Departments -->
                        <div class="user-stats" style="margin-top: 20px;">
                            <h3>🏢 Departments</h3>
                            ${this.data.stats.departments.map(dept => `
                                <div style="padding: 5px 0;">
                                    <span style="padding: 2px 6px; background: #f8f9fa; border-radius: 3px; font-size: 0.9em;">${dept}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;

            // Setup form submission
            const form = document.getElementById('create-user-form');
            if (form) {
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const formData = new FormData(form);
                    const userData = Object.fromEntries(formData);
                    this.createUser(userData);
                });
            }
        }

        toggleCreateForm() {
            const form = document.getElementById('create-form');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }

        editUser(userId) {
            const user = this.data.users.find(u => u.id === userId);
            if (user) {
                alert(`Edit user: ${user.full_name} (${user.username})`);
                // TODO: Implement edit user modal/form
            }
        }

        async toggleUserStatus(userId) {
            const user = this.data.users.find(u => u.id === userId);
            if (user) {
                const newStatus = user.status === 'active' ? 'suspended' : 'active';
                if (confirm(`${newStatus === 'suspended' ? 'Suspend' : 'Activate'} user ${user.full_name}?`)) {
                    // Update local data for immediate feedback
                    user.status = newStatus;
                    this.render();
                    
                    // TODO: Send API request to update status
                    console.log(`User ${user.username} status changed to ${newStatus}`);
                }
            }
        }
    }

    // Initialize when this component is loaded
    if (document.getElementById('users-content')) {
        window.userMgmt = new UserManagementComponent();
    }
</script>
        """
        return web.Response(text=html, content_type="text/html")


class UserManagementComponent(Component[GetUsers | CreateUser]):
    """User management component for user accounts and roles."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False

    async def on_start(self) -> None:
        await super().on_start()
        if not self.registered:
            # Register user management routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/users/data", view=UserManagementAPIView))
                await ctx.process(RegisterView(route="/components/users", view=UserManagementComponentView))

            self.registered = True
            print("👥 User Management component routes registered")

    async def handle(
        self, message: GetUsers | CreateUser, *, handler: Callable[[Message], Awaitable[None]], **_: Any
    ) -> None:
        """Handle user management requests."""
        if isinstance(message, GetUsers):
            # Handle get users request
            pass
        elif isinstance(message, CreateUser):
            # Handle user creation
            await handler(UserCreated(user_id="123", username=message.username))
