use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::any::Any;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
}

impl Message {
    pub fn new() -> Self {
        Self {
            id: Uuid::new_v4(),
            created_at: Utc::now(),
        }
    }
}

pub trait Command: Send + Sync + std::fmt::Debug {
    fn as_any(&self) -> &dyn Any;
    fn message(&self) -> &Message;
}

pub trait Query: Send + Sync + std::fmt::Debug {
    fn as_any(&self) -> &dyn Any;
    fn message(&self) -> &Message;
}

pub trait Event: Send + Sync + std::fmt::Debug {
    fn as_any(&self) -> &dyn Any;
    fn message(&self) -> &Message;
}

#[derive(Debug, Clone)]
pub struct SuccessEvent {
    pub message: Message,
}

impl SuccessEvent {
    pub fn new() -> Self {
        Self {
            message: Message::new(),
        }
    }
}

impl Event for SuccessEvent {
    fn as_any(&self) -> &dyn Any {
        self
    }
    
    fn message(&self) -> &Message {
        &self.message
    }
}

#[derive(Debug, Clone)]
pub struct FailureEvent {
    pub message: Message,
    pub error: String,
}

impl FailureEvent {
    pub fn new(error: String) -> Self {
        Self {
            message: Message::new(),
            error,
        }
    }
}

impl Event for FailureEvent {
    fn as_any(&self) -> &dyn Any {
        self
    }
    
    fn message(&self) -> &Message {
        &self.message
    }
}