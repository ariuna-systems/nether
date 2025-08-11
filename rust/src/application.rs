use crate::mediator::Mediator;
use crate::service::{HttpService, Service};
use anyhow::Result;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::signal;
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};

pub struct Application {
    mediator: Arc<RwLock<Mediator>>,
    configuration: HashMap<String, String>,
    stop_signal: Arc<RwLock<bool>>,
}

impl Application {
    pub fn new(configuration: HashMap<String, String>) -> Self {
        Self {
            mediator: Arc::new(RwLock::new(Mediator::new())),
            configuration,
            stop_signal: Arc::new(RwLock::new(false)),
        }
    }

    pub async fn register_service(&self, service: Box<dyn Service>) {
        let mut mediator = self.mediator.write().await;
        mediator.register_service(service);
    }

    pub async fn start(&mut self) -> Result<()> {
        tracing::info!("Starting application");

        // Setup signal handlers
        self.setup_signal_handlers().await;

        // Register default services
        let host = self.configuration
            .get("host")
            .map(|h| h.clone())
            .unwrap_or_else(|| "127.0.0.1".to_string());
        
        let port: u16 = self.configuration
            .get("port")
            .and_then(|p| p.parse().ok())
            .unwrap_or(8090);

        // Validate the host address format
        let validated_host = if host == "localhost" {
            "127.0.0.1".to_string()
        } else {
            host
        };

        tracing::info!("Configuring HTTP service on {}:{}", validated_host, port);

        let mut http_service = HttpService::new(validated_host, port, Some("static".to_string()));
        http_service.set_mediator(self.mediator.clone());
        self.register_service(Box::new(http_service)).await;

        // Start all services
        {
            let mut mediator = self.mediator.write().await;
            mediator.start_all_services().await?;
        }

        // Main application logic
        self.main().await?;

        // Application main loop
        while !*self.stop_signal.read().await {
            let running_count = {
                let mediator = self.mediator.read().await;
                mediator.running_services_count()
            };

            if running_count == 0 {
                break;
            }

            sleep(Duration::from_millis(500)).await;
        }

        // Stop all services
        {
            let mut mediator = self.mediator.write().await;
            mediator.stop_all_services().await?;
        }

        tracing::info!("Application finished");
        Ok(())
    }

    async fn setup_signal_handlers(&self) {
        let stop_signal = self.stop_signal.clone();
        
        tokio::spawn(async move {
            match signal::ctrl_c().await {
                Ok(()) => {
                    tracing::info!("Received Ctrl+C, shutting down gracefully");
                    *stop_signal.write().await = true;
                }
                Err(err) => {
                    tracing::error!("Failed to listen for shutdown signal: {}", err);
                }
            }
        });
    }

    async fn main(&self) -> Result<()> {
        tracing::info!("Application main logic executing");
        
        // Create a context and send some example messages
        let context = {
            let mut mediator = self.mediator.write().await;
            mediator.create_context().await
        };

        // Example: Send a start server command with validated address
        let start_cmd = crate::service::StartServerCommand {
            message: crate::common::Message::new(),
            host: "127.0.0.1".to_string(),
            port: 8080,
        };

        {
            let mut mediator = self.mediator.write().await;
            mediator.handle_message(Box::new(start_cmd), context.clone()).await?;
        }

        Ok(())
    }
}