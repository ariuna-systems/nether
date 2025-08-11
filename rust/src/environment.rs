use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::Path;

pub struct EnvironmentLoader {
    path: String,
}

impl EnvironmentLoader {
    pub fn new(path: &str) -> Self {
        Self {
            path: path.to_string(),
        }
    }

    pub fn load(&self) {
        if !Path::new(&self.path).exists() {
            return;
        }

        if let Ok(content) = fs::read_to_string(&self.path) {
            for line in content.lines() {
                let line = line.trim();
                if line.is_empty() || line.starts_with('#') {
                    continue;
                }

                if let Some((key, value)) = line.split_once('=') {
                    let key = key.trim();
                    let value = value.trim().trim_matches('"').trim_matches('\'');
                    
                    if env::var(key).is_err() {
                        env::set_var(key, value);
                    }
                }
            }
        }
    }

    pub fn load_from_dict(env_dict: HashMap<String, String>) {
        for (key, value) in env_dict {
            if !key.is_empty() && env::var(&key).is_err() {
                env::set_var(key, value);
            }
        }
    }

    pub fn validate<T>(key: &str, default: Option<T>, required: bool) -> Result<T, String> 
    where
        T: std::str::FromStr + Clone,
        T::Err: std::fmt::Display,
    {
        match env::var(key) {
            Ok(value) if !value.is_empty() => {
                value.parse().map_err(|e| {
                    format!("Environment variable {} must be valid: {}", key, e)
                })
            }
            Ok(_) | Err(_) => {
                if required {
                    Err(format!("Missing required environment variable: {}", key))
                } else if let Some(default_val) = default {
                    Ok(default_val)
                } else {
                    Err(format!("No default value provided for {}", key))
                }
            }
        }
    }

    pub fn validate_bool(key: &str, default: Option<bool>, required: bool) -> Result<bool, String> {
        match env::var(key) {
            Ok(value) if !value.is_empty() => {
                match value.to_lowercase().as_str() {
                    "true" | "1" | "yes" | "on" => Ok(true),
                    "false" | "0" | "no" | "off" => Ok(false),
                    _ => Err(format!("Environment variable {} must be a boolean", key)),
                }
            }
            Ok(_) | Err(_) => {
                if required {
                    Err(format!("Missing required environment variable: {}", key))
                } else if let Some(default_val) = default {
                    Ok(default_val)
                } else {
                    Err(format!("No default value provided for {}", key))
                }
            }
        }
    }
}