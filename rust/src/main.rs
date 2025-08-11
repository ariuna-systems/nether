mod application;
mod common;
mod mediator;
mod service;
mod environment;

use application::Application;
use anyhow::Result;
use std::collections::HashMap;
use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Load environment variables
    let env_loader = environment::EnvironmentLoader::new(".env");
    env_loader.load();

    // Create configuration
    let mut config = HashMap::new();
    config.insert("host".to_string(), "localhost".to_string());
    config.insert("port".to_string(), "8080".to_string());

    // Create and run application
    let mut app = Application::new(config);
    app.start().await?;

    Ok(())
}