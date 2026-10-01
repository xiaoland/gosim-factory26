use super::*;
use crate::objects::maintenance::{MaintenanceApply, NativeMaintenanceSource};

#[derive(Subcommand)]
pub enum MaintenanceCommand {
    Snapshot {
        #[arg(long)]
        operation_id: String,
        #[arg(long)]
        native_source: PathBuf,
    },
    Apply {
        #[arg(long)]
        input: PathBuf,
    },
    Receipt {
        operation_id: String,
    },
}

pub fn run(objects: &LocalObjects, turn: Option<&str>, command: MaintenanceCommand) -> Result<()> {
    match command {
        MaintenanceCommand::Snapshot { operation_id, native_source } => {
            let source: NativeMaintenanceSource =
                serde_json::from_slice(&fs::read(native_source)?)?;
            output(objects.maintenance_snapshot(turn, &operation_id, source)?)
        }
        MaintenanceCommand::Apply { input } => {
            let request: MaintenanceApply = serde_json::from_slice(&fs::read(input)?)?;
            output(objects.maintenance_apply(turn, request)?)
        }
        MaintenanceCommand::Receipt { operation_id } => {
            output(objects.maintenance_receipt(&operation_id)?)
        }
    }
}
