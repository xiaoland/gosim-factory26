//! Scheduler: Event Queue decisions. This module never touches provider
//! sessions or connections; it owns claims, quiet-window policy, context
//! pressure policy, and store-side fencing only.
use anyhow::{Context as _, Result};

use crate::{
    config::Config,
    context::{ContextPressure, RenderedContext},
    store::{SchedulerPolicy, StoreActor},
};

pub(crate) fn policy_from_config(config: &Config) -> SchedulerPolicy {
    SchedulerPolicy {
        quiet_seconds: config.scheduler.quiet_seconds,
        event_threshold: config.scheduler.event_threshold,
    }
}

pub(crate) fn record_context_pressure(
    store: &StoreActor,
    assignment_id: &str,
    rendered: &RenderedContext,
    error: Option<String>,
) -> Result<()> {
    tracing::info!(assignment_id, tier = ?rendered.tier, estimated_tokens = rendered.estimated_tokens, bytes = rendered.bytes, "context rendered");
    let pressure = match rendered.pressure {
        ContextPressure::Normal => "normal",
        ContextPressure::Soft => "soft",
        ContextPressure::Hard => "hard",
    };
    store.set_assignment_context_pressure(
        assignment_id.into(),
        pressure.into(),
        Some(u64::try_from(rendered.bytes).context("Context byte count exceeds u64")?),
        error,
    )?;
    Ok(())
}
