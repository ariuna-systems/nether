# Nether Module Creation Guide

This guide shows how to create a custom Nether module with REST API endpoints and web UI components.

## Table of Contents

1. [Module Structure](#module-structure)
2. [Step-by-Step Creation](#step-by-step-creation)
3. [REST API Implementation](#rest-api-implementation)
4. [Web Component UI](#web-component-ui)
5. [Module Registration](#module-registration)
6. [Complete Example](#complete-example)
7. [Testing Your Module](#testing-your-module)

## Module Structure

A Nether module consists of:

```
nether_system/module/your_module/
├── __init__.py          # Main module file with API views and web component
└── README.md           # Module documentation (optional)
```

## Step-by-Step Creation

### 1. Create Module Directory

```powershell
# Navigate to your nether system directory
cd c:\Users\david\projects\arjuna.group\nether\examples\system

# Create new module directory
New-Item -ItemType Directory -Path "nether_system\module\tasks"
```

### 2. Define Message Types

Create your module's message types (Commands, Events, Queries):

```python
from dataclasses import dataclass
from typing import Any
from nether.message import Command, Event, Query

@dataclass(frozen=True, kw_only=True, slots=True)
class CreateTask(Command):
    """Command to create a new task."""
    title: str
    description: str
    priority: str = "medium"

@dataclass(frozen=True, kw_only=True, slots=True)
class TaskCreated(Event):
    """Event when a task is created."""
    task_id: str
    task_data: dict[str, Any]

@dataclass(frozen=True, kw_only=True, slots=True)
class GetTasks(Query):
    """Query to get all tasks."""
    status: str | None = None
```

### 3. Create REST API Views

Define your API endpoints using aiohttp views:

```python
from aiohttp import web

class TaskAPIView(web.View):
    """REST API endpoints for task operations."""

    async def get(self) -> web.Response:
        """Get all tasks with optional filtering."""
        # Get query parameters
        status = self.request.query.get('status')
        
        # Mock data - replace with actual data access
        tasks = [
            {
                "id": "1",
                "title": "Complete project setup",
                "description": "Set up the initial project structure",
                "status": "in_progress",
                "priority": "high",
                "created_at": "2025-09-28T10:00:00Z",
                "updated_at": "2025-09-28T10:00:00Z"
            },
            {
                "id": "2", 
                "title": "Write documentation",
                "description": "Create user documentation",
                "status": "pending",
                "priority": "medium",
                "created_at": "2025-09-28T11:00:00Z",
                "updated_at": "2025-09-28T11:00:00Z"
            }
        ]
        
        # Filter by status if provided
        if status:
            tasks = [task for task in tasks if task["status"] == status]
            
        return web.json_response({
            "tasks": tasks,
            "total": len(tasks),
            "status": "success"
        })

    async def post(self) -> web.Response:
        """Create a new task."""
        try:
            data = await self.request.json()
            
            # Validate required fields
            if not data.get("title"):
                return web.json_response(
                    {"error": "Title is required"}, 
                    status=400
                )
            
            # Create new task (mock implementation)
            new_task = {
                "id": str(int(time.time())),
                "title": data["title"],
                "description": data.get("description", ""),
                "status": "pending",
                "priority": data.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # In a real implementation, you would:
            # 1. Send CreateTask command via mediator
            # 2. Save to database
            # 3. Emit TaskCreated event
            
            return web.json_response({
                "task": new_task,
                "status": "created"
            }, status=201)
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

    async def put(self) -> web.Response:
        """Update an existing task."""
        try:
            task_id = self.request.match_info.get('id')
            data = await self.request.json()
            
            # Mock update logic
            updated_task = {
                "id": task_id,
                "title": data.get("title", "Updated task"),
                "description": data.get("description", ""),
                "status": data.get("status", "pending"),
                "priority": data.get("priority", "medium"),
                "updated_at": datetime.now().isoformat()
            }
            
            return web.json_response({
                "task": updated_task,
                "status": "updated"
            })
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

    async def delete(self) -> web.Response:
        """Delete a task."""
        try:
            task_id = self.request.match_info.get('id')
            
            # Mock deletion logic
            return web.json_response({
                "message": f"Task {task_id} deleted successfully",
                "status": "deleted"
            })
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )
```

## Web Component UI

### 4. Create Web Component View

Create a view that serves your JavaScript web component:

```python
class TaskModuleView(web.View):
    """Serve the Task web component as ES6 module."""

    async def get(self) -> web.Response:
        """Return the Task web component JavaScript."""
        
        module_code = '''
        // Task Management Web Component
        class TaskWebComponent extends HTMLElement {
            constructor() {
                super();
                this.tasks = [];
                this.loadTasks();
            }

            connectedCallback() {
                this.render();
                this.attachEventListeners();
            }

            async loadTasks() {
                try {
                    const response = await fetch('/api/tasks');
                    const data = await response.json();
                    this.tasks = data.tasks || [];
                    this.render();
                } catch (error) {
                    console.error('Failed to load tasks:', error);
                    this.showError('Failed to load tasks');
                }
            }

            async createTask(taskData) {
                try {
                    const response = await fetch('/api/tasks', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(taskData)
                    });
                    
                    if (response.ok) {
                        await this.loadTasks(); // Refresh task list
                        this.showSuccess('Task created successfully');
                        this.resetForm();
                    } else {
                        const error = await response.json();
                        this.showError(error.error || 'Failed to create task');
                    }
                } catch (error) {
                    console.error('Failed to create task:', error);
                    this.showError('Failed to create task');
                }
            }

            async updateTaskStatus(taskId, status) {
                try {
                    const response = await fetch(`/api/tasks/${taskId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ status })
                    });
                    
                    if (response.ok) {
                        await this.loadTasks();
                        this.showSuccess('Task updated successfully');
                    }
                } catch (error) {
                    console.error('Failed to update task:', error);
                    this.showError('Failed to update task');
                }
            }

            render() {
                this.innerHTML = `
                    <div class="task-manager">
                        <div class="task-header">
                            <h2>Task Manager</h2>
                            <button id="addTaskBtn" class="btn-primary">Add Task</button>
                        </div>
                        
                        <div id="taskForm" class="task-form" style="display: none;">
                            <div class="form-group">
                                <label for="taskTitle">Title:</label>
                                <input type="text" id="taskTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="taskDescription">Description:</label>
                                <textarea id="taskDescription" rows="3"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="taskPriority">Priority:</label>
                                <select id="taskPriority">
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div class="form-actions">
                                <button id="saveTaskBtn" class="btn-primary">Save Task</button>
                                <button id="cancelTaskBtn" class="btn-secondary">Cancel</button>
                            </div>
                        </div>

                        <div class="task-filters">
                            <button class="filter-btn active" data-status="">All</button>
                            <button class="filter-btn" data-status="pending">Pending</button>
                            <button class="filter-btn" data-status="in_progress">In Progress</button>
                            <button class="filter-btn" data-status="completed">Completed</button>
                        </div>

                        <div id="messageArea" class="message-area"></div>

                        <div class="task-list">
                            ${this.renderTasks()}
                        </div>
                    </div>

                    <style>
                        .task-manager {
                            padding: 20px;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        }
                        
                        .task-header {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin-bottom: 20px;
                            padding-bottom: 15px;
                            border-bottom: 2px solid #e1e5e9;
                        }
                        
                        .task-header h2 {
                            color: #2c3e50;
                            margin: 0;
                        }
                        
                        .btn-primary {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                            transition: all 0.3s ease;
                        }
                        
                        .btn-primary:hover {
                            transform: translateY(-2px);
                            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                        }
                        
                        .btn-secondary {
                            background: #95a5a6;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                            margin-left: 10px;
                        }
                        
                        .task-form {
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            border: 1px solid #e1e5e9;
                        }
                        
                        .form-group {
                            margin-bottom: 15px;
                        }
                        
                        .form-group label {
                            display: block;
                            margin-bottom: 5px;
                            font-weight: 500;
                            color: #2c3e50;
                        }
                        
                        .form-group input,
                        .form-group textarea,
                        .form-group select {
                            width: 100%;
                            padding: 10px;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            font-size: 14px;
                        }
                        
                        .task-filters {
                            display: flex;
                            gap: 10px;
                            margin-bottom: 20px;
                        }
                        
                        .filter-btn {
                            padding: 8px 16px;
                            border: 1px solid #ddd;
                            background: white;
                            border-radius: 20px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        }
                        
                        .filter-btn:hover {
                            background: #f8f9fa;
                        }
                        
                        .filter-btn.active {
                            background: #667eea;
                            color: white;
                            border-color: #667eea;
                        }
                        
                        .task-item {
                            background: white;
                            border: 1px solid #e1e5e9;
                            border-radius: 8px;
                            padding: 15px;
                            margin-bottom: 10px;
                            transition: all 0.3s ease;
                        }
                        
                        .task-item:hover {
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                        }
                        
                        .task-title {
                            font-weight: 600;
                            color: #2c3e50;
                            margin-bottom: 8px;
                        }
                        
                        .task-description {
                            color: #7f8c8d;
                            margin-bottom: 10px;
                        }
                        
                        .task-meta {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            font-size: 12px;
                            color: #95a5a6;
                        }
                        
                        .priority-badge {
                            padding: 4px 8px;
                            border-radius: 12px;
                            font-size: 11px;
                            font-weight: 500;
                        }
                        
                        .priority-high { background: #e74c3c; color: white; }
                        .priority-medium { background: #f39c12; color: white; }
                        .priority-low { background: #27ae60; color: white; }
                        
                        .status-badge {
                            padding: 4px 8px;
                            border-radius: 12px;
                            font-size: 11px;
                            font-weight: 500;
                            cursor: pointer;
                        }
                        
                        .status-pending { background: #95a5a6; color: white; }
                        .status-in_progress { background: #3498db; color: white; }
                        .status-completed { background: #27ae60; color: white; }
                        
                        .message-area {
                            margin-bottom: 20px;
                            min-height: 20px;
                        }
                        
                        .message {
                            padding: 10px;
                            border-radius: 4px;
                            margin-bottom: 10px;
                        }
                        
                        .message.success {
                            background: #d4edda;
                            color: #155724;
                            border: 1px solid #c3e6cb;
                        }
                        
                        .message.error {
                            background: #f8d7da;
                            color: #721c24;
                            border: 1px solid #f5c6cb;
                        }
                    </style>
                `;
            }

            renderTasks() {
                if (this.tasks.length === 0) {
                    return '<div class="no-tasks">No tasks found. Create your first task!</div>';
                }

                return this.tasks.map(task => `
                    <div class="task-item">
                        <div class="task-title">${task.title}</div>
                        <div class="task-description">${task.description}</div>
                        <div class="task-meta">
                            <div>
                                <span class="priority-badge priority-${task.priority}">${task.priority}</span>
                                <span class="status-badge status-${task.status}" 
                                      onclick="this.getRootNode().host.toggleTaskStatus('${task.id}', '${task.status}')">
                                    ${task.status.replace('_', ' ')}
                                </span>
                            </div>
                            <div>Created: ${new Date(task.created_at).toLocaleDateString()}</div>
                        </div>
                    </div>
                `).join('');
            }

            attachEventListeners() {
                this.querySelector('#addTaskBtn').addEventListener('click', () => {
                    this.querySelector('#taskForm').style.display = 'block';
                });

                this.querySelector('#cancelTaskBtn').addEventListener('click', () => {
                    this.resetForm();
                });

                this.querySelector('#saveTaskBtn').addEventListener('click', () => {
                    this.handleSaveTask();
                });

                // Filter buttons
                this.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        this.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                        e.target.classList.add('active');
                        this.filterTasks(e.target.dataset.status);
                    });
                });
            }

            handleSaveTask() {
                const title = this.querySelector('#taskTitle').value.trim();
                const description = this.querySelector('#taskDescription').value.trim();
                const priority = this.querySelector('#taskPriority').value;

                if (!title) {
                    this.showError('Title is required');
                    return;
                }

                this.createTask({
                    title,
                    description,
                    priority
                });
            }

            resetForm() {
                this.querySelector('#taskForm').style.display = 'none';
                this.querySelector('#taskTitle').value = '';
                this.querySelector('#taskDescription').value = '';
                this.querySelector('#taskPriority').value = 'medium';
            }

            toggleTaskStatus(taskId, currentStatus) {
                const statusCycle = {
                    'pending': 'in_progress',
                    'in_progress': 'completed',
                    'completed': 'pending'
                };
                
                const newStatus = statusCycle[currentStatus];
                this.updateTaskStatus(taskId, newStatus);
            }

            filterTasks(status) {
                // In a more complex implementation, you would filter the displayed tasks
                // For now, we'll just reload with the filter
                console.log('Filtering tasks by status:', status);
            }

            showSuccess(message) {
                this.showMessage(message, 'success');
            }

            showError(message) {
                this.showMessage(message, 'error');
            }

            showMessage(message, type) {
                const messageArea = this.querySelector('#messageArea');
                messageArea.innerHTML = `<div class="message ${type}">${message}</div>`;
                
                // Auto-hide after 3 seconds
                setTimeout(() => {
                    messageArea.innerHTML = '';
                }, 3000);
            }
        }

        // Export and register the component
        export default TaskWebComponent;
        if (!customElements.get('task-component')) {
            customElements.define('task-component', TaskWebComponent);
        }
        '''

        return web.Response(
            text=module_code,
            content_type="application/javascript",
            headers={"Content-Security-Policy": "default-src 'self'"}
        )
```

## Module Registration

### 5. Create the Module Class

Create the main module class that handles registration and message processing:

```python
import time
from datetime import datetime
from collections.abc import Awaitable, Callable
from typing import Any

from nether.modules import Module
from nether.server import RegisterView

class TaskModule(Module[CreateTask | GetTasks | UpdateSettings]):
    """Task management module with REST API and web UI."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False
        # In a real implementation, you would initialize a database connection here
        self.tasks = []  # Mock storage

    async def on_start(self) -> None:
        """Initialize the module and register routes."""
        await super().on_start()
        
        if not self.registered:
            # Register API routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/tasks", view=TaskAPIView))
                await ctx.process(RegisterView(route="/api/tasks/{id}", view=TaskAPIView))
                await ctx.process(RegisterView(route="/modules/tasks.js", view=TaskModuleView))

            self.registered = True
            print("Task module routes registered")

    async def handle(
        self,
        message: CreateTask | GetTasks | UpdateSettings,
        *,
        handler: Callable[[Message], Awaitable[None]],
        **_: Any,
    ) -> None:
        """Handle task-related messages through the mediator."""
        
        if isinstance(message, CreateTask):
            # Handle task creation
            new_task = {
                "id": str(int(time.time())),
                "title": message.title,
                "description": message.description,
                "priority": message.priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.tasks.append(new_task)
            
            # Emit event
            event = TaskCreated(task_id=new_task["id"], task_data=new_task)
            async with self.application.mediator.context() as ctx:
                await ctx.publish(event)
                
        elif isinstance(message, GetTasks):
            # Handle task retrieval
            filtered_tasks = self.tasks
            if message.status:
                filtered_tasks = [task for task in self.tasks if task["status"] == message.status]
            
            # You could emit a TasksRetrieved event here if needed
            return filtered_tasks
```

## Complete Example

### 6. Put It All Together

Create the complete module file `nether_system/module/tasks/__init__.py`:

```python
"""
Task Management Module - Complete example with REST API and Web UI
"""

import time
from datetime import datetime
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiohttp import web
from nether.modules import Module
from nether.message import Command, Event, Query, Message
from nether.server import RegisterView

__all__ = ["TaskModule"]
__version__ = "1.0.0"

# Message Types
@dataclass(frozen=True, kw_only=True, slots=True)
class CreateTask(Command):
    """Command to create a new task."""
    title: str
    description: str
    priority: str = "medium"

@dataclass(frozen=True, kw_only=True, slots=True)
class TaskCreated(Event):
    """Event when a task is created."""
    task_id: str
    task_data: dict[str, Any]

@dataclass(frozen=True, kw_only=True, slots=True)
class GetTasks(Query):
    """Query to get all tasks."""
    status: str | None = None

# API Views
class TaskAPIView(web.View):
    """REST API endpoints for task operations."""

    async def get(self) -> web.Response:
        """Get all tasks with optional filtering."""
        # Get query parameters
        status = self.request.query.get('status')
        
        # Mock data - replace with actual data access
        tasks = [
            {
                "id": "1",
                "title": "Complete project setup",
                "description": "Set up the initial project structure",
                "status": "in_progress",
                "priority": "high",
                "created_at": "2025-09-28T10:00:00Z",
                "updated_at": "2025-09-28T10:00:00Z"
            },
            {
                "id": "2", 
                "title": "Write documentation",
                "description": "Create user documentation",
                "status": "pending",
                "priority": "medium",
                "created_at": "2025-09-28T11:00:00Z",
                "updated_at": "2025-09-28T11:00:00Z"
            }
        ]
        
        # Filter by status if provided
        if status:
            tasks = [task for task in tasks if task["status"] == status]
            
        return web.json_response({
            "tasks": tasks,
            "total": len(tasks),
            "status": "success"
        })

    async def post(self) -> web.Response:
        """Create a new task."""
        try:
            data = await self.request.json()
            
            # Validate required fields
            if not data.get("title"):
                return web.json_response(
                    {"error": "Title is required"}, 
                    status=400
                )
            
            # Create new task (mock implementation)
            new_task = {
                "id": str(int(time.time())),
                "title": data["title"],
                "description": data.get("description", ""),
                "status": "pending",
                "priority": data.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            return web.json_response({
                "task": new_task,
                "status": "created"
            }, status=201)
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

    async def put(self) -> web.Response:
        """Update an existing task."""
        try:
            task_id = self.request.match_info.get('id')
            data = await self.request.json()
            
            # Mock update logic
            updated_task = {
                "id": task_id,
                "title": data.get("title", "Updated task"),
                "description": data.get("description", ""),
                "status": data.get("status", "pending"),
                "priority": data.get("priority", "medium"),
                "updated_at": datetime.now().isoformat()
            }
            
            return web.json_response({
                "task": updated_task,
                "status": "updated"
            })
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

    async def delete(self) -> web.Response:
        """Delete a task."""
        try:
            task_id = self.request.match_info.get('id')
            
            # Mock deletion logic
            return web.json_response({
                "message": f"Task {task_id} deleted successfully",
                "status": "deleted"
            })
            
        except Exception as e:
            return web.json_response(
                {"error": str(e)}, 
                status=500
            )

# Web Component View
class TaskModuleView(web.View):
    """Serve the Task web component as ES6 module."""

    async def get(self) -> web.Response:
        """Return the Task web component JavaScript."""
        
        module_code = '''
        // Task Management Web Component
        class TaskWebComponent extends HTMLElement {
            constructor() {
                super();
                this.tasks = [];
                this.loadTasks();
            }

            connectedCallback() {
                this.render();
                this.attachEventListeners();
            }

            async loadTasks() {
                try {
                    const response = await fetch('/api/tasks');
                    const data = await response.json();
                    this.tasks = data.tasks || [];
                    this.render();
                } catch (error) {
                    console.error('Failed to load tasks:', error);
                    this.showError('Failed to load tasks');
                }
            }

            async createTask(taskData) {
                try {
                    const response = await fetch('/api/tasks', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(taskData)
                    });
                    
                    if (response.ok) {
                        await this.loadTasks();
                        this.showSuccess('Task created successfully');
                        this.resetForm();
                    } else {
                        const error = await response.json();
                        this.showError(error.error || 'Failed to create task');
                    }
                } catch (error) {
                    console.error('Failed to create task:', error);
                    this.showError('Failed to create task');
                }
            }

            render() {
                this.innerHTML = `
                    <div class="task-manager">
                        <div class="task-header">
                            <h2>Task Manager</h2>
                            <button id="addTaskBtn" class="btn-primary">Add Task</button>
                        </div>
                        
                        <div id="taskForm" class="task-form" style="display: none;">
                            <div class="form-group">
                                <label for="taskTitle">Title:</label>
                                <input type="text" id="taskTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="taskDescription">Description:</label>
                                <textarea id="taskDescription" rows="3"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="taskPriority">Priority:</label>
                                <select id="taskPriority">
                                    <option value="low">Low</option>
                                    <option value="medium" selected>Medium</option>
                                    <option value="high">High</option>
                                </select>
                            </div>
                            <div class="form-actions">
                                <button id="saveTaskBtn" class="btn-primary">Save Task</button>
                                <button id="cancelTaskBtn" class="btn-secondary">Cancel</button>
                            </div>
                        </div>

                        <div class="task-list">
                            ${this.renderTasks()}
                        </div>
                        
                        <div id="messageArea" class="message-area"></div>
                    </div>

                    <style>
                        .task-manager {
                            padding: 20px;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        }
                        
                        .task-header {
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin-bottom: 20px;
                            padding-bottom: 15px;
                            border-bottom: 2px solid #e1e5e9;
                        }
                        
                        .btn-primary {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                        }
                        
                        .btn-secondary {
                            background: #95a5a6;
                            color: white;
                            border: none;
                            padding: 10px 20px;
                            border-radius: 6px;
                            cursor: pointer;
                            margin-left: 10px;
                        }
                        
                        .task-form {
                            background: #f8f9fa;
                            padding: 20px;
                            border-radius: 8px;
                            margin-bottom: 20px;
                            border: 1px solid #e1e5e9;
                        }
                        
                        .form-group {
                            margin-bottom: 15px;
                        }
                        
                        .form-group label {
                            display: block;
                            margin-bottom: 5px;
                            font-weight: 500;
                        }
                        
                        .form-group input,
                        .form-group textarea,
                        .form-group select {
                            width: 100%;
                            padding: 10px;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                        }
                        
                        .task-item {
                            background: white;
                            border: 1px solid #e1e5e9;
                            border-radius: 8px;
                            padding: 15px;
                            margin-bottom: 10px;
                        }
                        
                        .message-area {
                            margin-top: 20px;
                        }
                        
                        .message {
                            padding: 10px;
                            border-radius: 4px;
                            margin-bottom: 10px;
                        }
                        
                        .message.success {
                            background: #d4edda;
                            color: #155724;
                            border: 1px solid #c3e6cb;
                        }
                        
                        .message.error {
                            background: #f8d7da;
                            color: #721c24;
                            border: 1px solid #f5c6cb;
                        }
                    </style>
                `;
            }

            renderTasks() {
                if (this.tasks.length === 0) {
                    return '<div class="no-tasks">No tasks found. Create your first task!</div>';
                }

                return this.tasks.map(task => `
                    <div class="task-item">
                        <h4>${task.title}</h4>
                        <p>${task.description}</p>
                        <div>Priority: ${task.priority} | Status: ${task.status}</div>
                    </div>
                `).join('');
            }

            attachEventListeners() {
                this.querySelector('#addTaskBtn').addEventListener('click', () => {
                    this.querySelector('#taskForm').style.display = 'block';
                });

                this.querySelector('#cancelTaskBtn').addEventListener('click', () => {
                    this.resetForm();
                });

                this.querySelector('#saveTaskBtn').addEventListener('click', () => {
                    this.handleSaveTask();
                });
            }

            handleSaveTask() {
                const title = this.querySelector('#taskTitle').value.trim();
                const description = this.querySelector('#taskDescription').value.trim();
                const priority = this.querySelector('#taskPriority').value;

                if (!title) {
                    this.showError('Title is required');
                    return;
                }

                this.createTask({
                    title,
                    description,
                    priority
                });
            }

            resetForm() {
                this.querySelector('#taskForm').style.display = 'none';
                this.querySelector('#taskTitle').value = '';
                this.querySelector('#taskDescription').value = '';
                this.querySelector('#taskPriority').value = 'medium';
            }

            showSuccess(message) {
                this.showMessage(message, 'success');
            }

            showError(message) {
                this.showMessage(message, 'error');
            }

            showMessage(message, type) {
                const messageArea = this.querySelector('#messageArea');
                messageArea.innerHTML = `<div class="message ${type}">${message}</div>`;
                
                setTimeout(() => {
                    messageArea.innerHTML = '';
                }, 3000);
            }
        }

        export default TaskWebComponent;
        if (!customElements.get('task-component')) {
            customElements.define('task-component', TaskWebComponent);
        }
        '''

        return web.Response(
            text=module_code,
            content_type="application/javascript",
            headers={"Content-Security-Policy": "default-src 'self'"}
        )

# Main Module Class
class TaskModule(Module[CreateTask | GetTasks]):
    """Task management module with REST API and web UI."""

    def __init__(self, application):
        super().__init__(application)
        self.registered = False
        self.tasks = []  # Mock storage

    async def on_start(self) -> None:
        """Initialize the module and register routes."""
        await super().on_start()
        
        if not self.registered:
            # Register API routes
            async with self.application.mediator.context() as ctx:
                await ctx.process(RegisterView(route="/api/tasks", view=TaskAPIView))
                await ctx.process(RegisterView(route="/api/tasks/{id}", view=TaskAPIView))
                await ctx.process(RegisterView(route="/modules/tasks.js", view=TaskModuleView))

            self.registered = True
            print("Task module routes registered")

    async def handle(
        self,
        message: CreateTask | GetTasks,
        *,
        handler: Callable[[Message], Awaitable[None]],
        **_: Any,
    ) -> None:
        """Handle task-related messages through the mediator."""
        
        if isinstance(message, CreateTask):
            new_task = {
                "id": str(int(time.time())),
                "title": message.title,
                "description": message.description,
                "priority": message.priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.tasks.append(new_task)
            
            # Emit event
            event = TaskCreated(task_id=new_task["id"], task_data=new_task)
            async with self.application.mediator.context() as ctx:
                await ctx.publish(event)
                
        elif isinstance(message, GetTasks):
            filtered_tasks = self.tasks
            if message.status:
                filtered_tasks = [task for task in self.tasks if task["status"] == message.status]
            
            return filtered_tasks
```

## Register Your Module

### 7. Add Module to System

Add your new module to the main system in `nether_system/__init__.py`:

```python
# Import your module
from .module.tasks import TaskModule

# In the System.register_components method, add:
async def register_components(self):
    # ... existing modules ...
    
    # Add your task module
    tasks = TaskModule(self)
    self.attach(tasks)
    self.component_registry.register_component(
        "tasks",
        tasks,
        {
            "id": "tasks",
            "name": "Task Manager", 
            "description": "Task management and tracking",
            "version": "1.0.0",
            "tag_name": "task-component",
            "class_name": "TaskWebComponent",
            "routes": {
                "api_base": "/api/tasks",
                "web_component": "/components/tasks",
                "module": "/modules/tasks.js",
            },
            "menu": {
                "title": "Tasks",
                "icon": "task",
                "order": 4,
                "route": "/tasks",
            },
            "permissions": ["read:tasks", "write:tasks"],
            "api_endpoints": [
                "/api/tasks",
                "/api/tasks/{id}"
            ],
        },
    )
```

## Testing Your Module

### 8. Run and Test

```powershell
# Navigate to your project directory
cd c:\Users\david\projects\arjuna.group\nether\examples\system

# Run the system
python -m nether-system
```

Your module will be available at:

- **Web UI**: `http://localhost:8000` (Tasks will appear in the navigation)
- **REST API**:
  - `GET http://localhost:8000/api/tasks` - List all tasks
  - `POST http://localhost:8000/api/tasks` - Create new task
  - `PUT http://localhost:8000/api/tasks/{id}` - Update task
  - `DELETE http://localhost:8000/api/tasks/{id}` - Delete task

### 9. API Testing Examples

```powershell
# Create a new task
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks" -Method POST -ContentType "application/json" -Body '{"title": "Test Task", "description": "Testing the API", "priority": "high"}'

# Get all tasks
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks" -Method GET

# Get tasks by status
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks?status=pending" -Method GET
```

## Key Points

1. **Message Types**: Define your Commands, Events, and Queries using dataclasses
2. **API Views**: Use aiohttp web.View classes for REST endpoints
3. **Web Components**: Create ES6 modules with custom HTML elements
4. **Module Registration**: Register routes in the `on_start` method
5. **Message Handling**: Implement the `handle` method for mediator communication
6. **System Integration**: Add your module to the main system registration

This pattern allows you to create fully modular, pluggable components with both backend logic and frontend UI that integrate seamlessly with the Nether framework architecture.
