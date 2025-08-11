use crate::common::{Command, Event, Query};
use crate::service::Service;
use anyhow::Result;
use std::any::TypeId;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use uuid::Uuid;

pub struct MediatorContext {
    pub id: Uuid,
    pub event_sender: mpsc::UnboundedSender<Box<dyn Event>>,
    pub event_receiver: Arc<RwLock<mpsc::UnboundedReceiver<Box<dyn Event>>>>,
}

impl MediatorContext {
    pub fn new() -> Self {
        let (event_sender, event_receiver) = mpsc::unbounded_channel();
        Self {
            id: Uuid::new_v4(),
            event_sender,
            event_receiver: Arc::new(RwLock::new(event_receiver)),
        }
    }

    pub async fn dispatch_event(&self, event: Box<dyn Event>) -> Result<()> {
        self.event_sender.send(event)?;
        Ok(())
    }

    pub async fn receive_event(&self) -> Option<Box<dyn Event>> {
        let mut receiver = self.event_receiver.write().await;
        receiver.recv().await
    }
}

pub struct Mediator {
    services: Vec<Box<dyn Service>>,
    contexts: HashMap<Uuid, Arc<MediatorContext>>,
}

impl Mediator {
    pub fn new() -> Self {
        Self {
            services: Vec::new(),
            contexts: HashMap::new(),
        }
    }

    pub fn register_service(&mut self, service: Box<dyn Service>) {
        tracing::info!("Registering service");
        self.services.push(service);
    }

    pub fn unregister_service(&mut self, _service_id: Uuid) {
        // Implementation for unregistering services
        tracing::info!("Unregistering service");
    }

    pub async fn create_context(&mut self) -> Arc<MediatorContext> {
        let context = Arc::new(MediatorContext::new());
        self.contexts.insert(context.id, context.clone());
        context
    }

    pub async fn remove_context(&mut self, context_id: Uuid) {
        self.contexts.remove(&context_id);
    }

    pub async fn handle_message(
        &mut self,
        message: Box<dyn std::any::Any + Send>,
        context: Arc<MediatorContext>,
    ) -> Result<()> {
        let message_type = (&*message).type_id();
        let mut handled = false;

        for service in &mut self.services {
            if service.supports().contains(&message_type) {
                service.handle(message, context.clone()).await?;
                handled = true;
                break;
            }
        }

        if !handled {
            tracing::warn!("No handler found for message type: {:?}", message_type);
        }

        Ok(())
    }

    pub async fn start_all_services(&mut self) -> Result<()> {
        for service in &mut self.services {
            service.start().await?;
        }
        Ok(())
    }

    pub async fn stop_all_services(&mut self) -> Result<()> {
        for service in &mut self.services {
            service.stop().await?;
        }
        Ok(())
    }

    pub fn running_services_count(&self) -> usize {
        self.services.iter().filter(|s| s.is_running()).count()
    }

    pub async fn get_services_info(&self) -> Vec<crate::service::ServiceInfo> {
        self.services.iter().enumerate().map(|(index, service)| {
            let supported_types: Vec<String> = service.supports()
                .iter()
                .map(|type_id| format!("{:?}", type_id))
                .collect();

            crate::service::ServiceInfo {
                name: format!("Service_{}", index), // You can enhance this with actual service names
                is_running: service.is_running(),
                supported_types,
            }
        }).collect()
    }
}