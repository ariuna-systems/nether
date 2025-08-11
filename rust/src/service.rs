use crate::common::{Command, Event, Query};
use crate::mediator::MediatorContext;
use async_trait::async_trait;
use std::any::TypeId;
use std::collections::HashSet;
use std::sync::Arc;
use tokio::sync::RwLock;
use anyhow::Result;
use warp::Filter;
use tokio::task::JoinHandle;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct ServiceInfo {
    pub name: String,
    pub is_running: bool,
    pub supported_types: Vec<String>,
}

#[derive(Serialize)]
pub struct ServicesResponse {
    pub services: Vec<ServiceInfo>,
    pub total_count: usize,
    pub running_count: usize,
}

#[async_trait]
pub trait Service: Send + Sync {
    fn supports(&self) -> HashSet<TypeId>;
    fn is_running(&self) -> bool;
    async fn start(&mut self) -> Result<()>;
    async fn stop(&mut self) -> Result<()>;
    async fn handle(
        &mut self,
        message: Box<dyn std::any::Any + Send>,
        context: Arc<MediatorContext>,
    ) -> Result<()>;
}

pub struct BaseService {
    pub is_running: bool,
    pub supported_types: HashSet<TypeId>,
}

impl BaseService {
    pub fn new() -> Self {
        Self {
            is_running: false,
            supported_types: HashSet::new(),
        }
    }

    pub fn add_support<T: 'static>(&mut self) {
        self.supported_types.insert(TypeId::of::<T>());
    }
}

// Enhanced HTTP service that serves static files
pub struct HttpService {
    base: BaseService,
    host: String,
    port: u16,
    static_dir: String,
    server_handle: Option<JoinHandle<()>>,
    shutdown_sender: Option<tokio::sync::oneshot::Sender<()>>,
    mediator: Option<Arc<RwLock<crate::mediator::Mediator>>>,
}

impl HttpService {
    pub fn new(host: String, port: u16, static_dir: Option<String>) -> Self {
        let mut base = BaseService::new();
        base.add_support::<StartServerCommand>();
        base.add_support::<StopServerCommand>();
        
        Self { 
            base, 
            host, 
            port,
            static_dir: static_dir.unwrap_or_else(|| "static".to_string()),
            server_handle: None,
            shutdown_sender: None,
            mediator: None,
        }
    }

    pub fn set_mediator(&mut self, mediator: Arc<RwLock<crate::mediator::Mediator>>) {
        self.mediator = Some(mediator);
    }

    async fn start_server(&mut self) -> Result<()> {
        let (shutdown_tx, shutdown_rx) = tokio::sync::oneshot::channel();
        self.shutdown_sender = Some(shutdown_tx);

        let static_dir = self.static_dir.clone();
        let host = self.host.clone();
        let port = self.port;
        let mediator = self.mediator.clone();

        // Create static file routes
        let static_files = warp::fs::dir(static_dir.clone());
        
        // Route for root path to serve index.html
        let index = warp::path::end()
            .and(warp::fs::file(format!("{}/index.html", static_dir)));

        // API route for listing services
        let services_route = warp::path("api")
            .and(warp::path("services"))
            .and(warp::path::end())
            .and(warp::get())
            .and_then({
                let mediator = mediator.clone();
                move || {
                    let mediator = mediator.clone();
                    async move {
                        if let Some(mediator) = mediator {
                            match get_services_info(mediator).await {
                                Ok(response) => Ok(warp::reply::json(&response)),
                                Err(_) => Err(warp::reject::custom(ApiError::InternalError))
                            }
                        } else {
                            Err(warp::reject::custom(ApiError::ServiceUnavailable))
                        }
                    }
                }
            });

        // Combine all routes
        let routes = index
            .or(services_route)
            .or(static_files)
            .with(warp::cors().allow_any_origin().allow_headers(vec!["content-type"]).allow_methods(vec!["GET"]));

        // Convert host string to SocketAddr with better error handling
        let addr_str = format!("{}:{}", host, port);
        let addr: std::net::SocketAddr = addr_str.parse()
            .map_err(|e| anyhow::anyhow!("Invalid socket address '{}': {}", addr_str, e))?;

        tracing::info!("Binding HTTP server to {} with API routes", addr);

        let (_, server) = warp::serve(routes)
            .bind_with_graceful_shutdown(addr, async {
                shutdown_rx.await.ok();
            });

        let handle = tokio::spawn(server);
        self.server_handle = Some(handle);

        Ok(())
    }

    async fn stop_server(&mut self) -> Result<()> {
        if let Some(sender) = self.shutdown_sender.take() {
            let _ = sender.send(());
        }

        if let Some(handle) = self.server_handle.take() {
            handle.abort();
        }

        Ok(())
    }
}

// Helper function to get services information
async fn get_services_info(mediator: Arc<RwLock<crate::mediator::Mediator>>) -> Result<ServicesResponse> {
    let mediator = mediator.read().await;
    let services_info = mediator.get_services_info().await;
    let running_count = mediator.running_services_count();
    
    Ok(ServicesResponse {
        total_count: services_info.len(),
        running_count,
        services: services_info,
    })
}

// Custom error types for API
#[derive(Debug)]
enum ApiError {
    InternalError,
    ServiceUnavailable,
}

impl warp::reject::Reject for ApiError {}

// Example commands
#[derive(Debug)]
pub struct StartServerCommand {
    pub message: crate::common::Message,
    pub host: String,
    pub port: u16,
}

impl Command for StartServerCommand {
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }
    
    fn message(&self) -> &crate::common::Message {
        &self.message
    }
}

#[derive(Debug)]
pub struct StopServerCommand {
    pub message: crate::common::Message,
}

impl Command for StopServerCommand {
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }
    
    fn message(&self) -> &crate::common::Message {
        &self.message
    }
}

#[async_trait]
impl Service for HttpService {
    fn supports(&self) -> HashSet<TypeId> {
        self.base.supported_types.clone()
    }

    fn is_running(&self) -> bool {
        self.base.is_running
    }

    async fn start(&mut self) -> Result<()> {
        if !self.base.is_running {
            tracing::info!("Starting HTTP service on {}:{}, serving from {}", 
                          self.host, self.port, self.static_dir);
            
            self.start_server().await?;
            self.base.is_running = true;
            
            tracing::info!("HTTP service started successfully");
        }
        Ok(())
    }

    async fn stop(&mut self) -> Result<()> {
        if self.base.is_running {
            tracing::info!("Stopping HTTP service");
            
            self.stop_server().await?;
            self.base.is_running = false;
            
            tracing::info!("HTTP service stopped");
        }
        Ok(())
    }

    async fn handle(
        &mut self,
        message: Box<dyn std::any::Any + Send>,
        context: Arc<MediatorContext>,
    ) -> Result<()> {
        if let Some(cmd) = message.downcast_ref::<StartServerCommand>() {
            tracing::info!("Handling start server command: {:?}", cmd);
            self.host = cmd.host.clone();
            self.port = cmd.port;
            self.start().await?;
        } else if let Some(cmd) = message.downcast_ref::<StopServerCommand>() {
            tracing::info!("Handling stop server command: {:?}", cmd);
            self.stop().await?;
        }
        Ok(())
    }
}