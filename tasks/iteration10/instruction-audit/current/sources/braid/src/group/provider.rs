use anyhow::Result;
use sha2::{Digest, Sha256};

use crate::{
    config::{Config, Profile, RuntimeBinding},
    store::{ProfileRecord, StoreActor, TurnClaim},
};

pub(crate) fn operational_status_unknown_profile(_profile_id: &str) -> String {
    format!(
        "> **本地运行状态**\n\n\
         **执行结果未知**\n\n\
         活动执行期间连接中断。系统没有启动并行执行，也没有把任务判为完成或失败；需要恢复或宿主修复。",
    )
}

pub(crate) fn materialized_profile(profile: &Profile) -> Result<ProfileRecord> {
    let bytes = serde_json::to_vec(profile)?;
    let digest = hex::encode(Sha256::digest(bytes));
    let revision = u64::from_str_radix(&digest[..15], 16)?.max(1);
    Ok(ProfileRecord {
        profile_id: profile.id.clone(),
        revision,
        effective_digest: digest,
        provider_kind: profile.adapter_type.clone(),
        tags: serde_json::to_string(&profile.tags)?,
        assignee_login: profile.assignee_login.clone(),
        assignee_description: profile.assignee_description.clone(),
    })
}

pub(crate) fn materialized_profile_with_binding(
    profile: &Profile,
    binding: &RuntimeBinding,
) -> Result<ProfileRecord> {
    let mut record = materialized_profile(profile)?;
    let digest = binding
        .capabilities
        .get("digest")
        .and_then(serde_json::Value::as_str)
        .map(str::to_owned)
        .unwrap_or_else(|| {
            let material = serde_json::json!({"profile": profile, "binding": binding});
            hex::encode(Sha256::digest(
                serde_json::to_vec(&material).expect("profile digest serializes"),
            ))
        });
    let revision = digest
        .get(..15)
        .and_then(|prefix| u64::from_str_radix(prefix, 16).ok())
        .unwrap_or_else(|| {
            let hash = Sha256::digest(digest.as_bytes());
            u64::from_str_radix(&hex::encode(hash)[..15], 16).unwrap_or(1)
        });
    record.revision = revision.max(1);
    record.effective_digest = digest;
    Ok(record)
}

fn local_instructions(config: &Config, profile: &Profile, role: &str, member_login: Option<&str>) -> String {
    let directory = config
        .profiles
        .iter()
        .filter(|member| !member.tags.iter().any(|tag| tag == "root-only"))
        .map(|member| format!("- {}：{}", member.assignee_login, member.assignee_description))
        .collect::<Vec<_>>()
        .join("\n");
    format!(
        "{role}\n你是 @{}。使用 `braid` CLI 操作 Issue / PR，常用操作沿用 GitHub CLI 的形式。Issue 和 PR 可以 assign 给其他 Agent；像人类一样在 Issue / PR 中开展协作。\n维护你负责的 Issue/PR，让接手者能找到当前有效的要求、决定和未决问题。description 保存当前任务说明与稳定决定，comment 承载讨论、证据和增量进展，相关回复用 `--reply-to` 留在同一 thread。形成新决定或发现旧判断失准时，先在原讨论说明更正和依据，并联系受影响成员；再窄改仍含有效信息的旧说明并留下更正链接，整条不再适用时用 `comment hide ID --reason TEXT` 隐藏并说明理由。问题解决后先保留仍需使用的结论和证据入口，再用 `comment resolve ID` 折叠已结束讨论，后续回复仍可见；未决分歧、风险和验收前提保持可见。交接前核对当前说明，无需把日常进度反复复制到正文。`issue view ID --comments`、`pr view ID --comments` 查看工作项，`comment view ID --thread` 查看整串，`--include-hidden` 可追溯隐藏内容。回复通知负责人、未退出关注的讨论参与者和显式关注者，@ 可联系其他具体成员。编辑、隐藏、折叠会影响后续重建的上下文，不会抹去在途成员已收到的信息；需及时纠偏时仍通过评论联系。`view ID --timeline` 可查看协作历史；`subscribe` / `unsubscribe` 可调整自己对工作项的关注；显式退出持续有效，单次 @ 仍送达但不会恢复关注，需主动 subscribe，负责人不能退订。PR 的 `--issue` / `link` 只关联需求与讨论背景；关闭意图写在 PR 正文中，如 `Closes #2`，合入 origin 默认分支时才关闭，合入其它分支不自动关闭。创建时从下方列表选一个名称填入 `--assignee`，之后可用 edit 的 `--add-assignee` / `--remove-assignee` 更换负责人。创建 Issue 或 PR 只建立工作项，指派即交给独立成员在自己的工作区推进，无需再替该成员启动执行。每次新指派会返回一位具体负责人；该成员名用于协作，不作为下一次 `--assignee` 的输入。完整参数见对应命令的 `--help`。\n当前目录是持续保留的 Git clone；用普通 `git commit` 和 `git push` 将成果发布到本次运行的 origin，再用 `git fetch` 取得其他 Agent 已发布的提交。\n可指派的 Agent：\n{directory}\n--- 用户指引 ---\n{}",
        member_login.unwrap_or("宿主绑定成员"),
        profile.user_instructions
    )
}
pub(crate) fn issue_system_prompt(config: &Config, profile: &Profile, number: u64, member_login: Option<&str>) -> String {
    local_instructions(
        config,
        profile,
        &format!(
            "你正在处理 Issue #{number}，负责产品需求、技术方案与验收方案的设计，并保留原始要求、重要决定和未决问题的入口。进入实施前，创建关联 PR 并指派负责人，把这些依据交给 PR 负责人；由其在独立工作区承接实现计划、预演排障、实现与验收，再将候选和结果交回；不要先在 Issue 中完成实现再把 PR 当作补办手续。你在 Issue 中处理设计问题、协作决定和返回的结果；需要调整方案时继续在相关讨论中协作。可创建和关联 PR、合并 ready PR；`braid issue close {number} --reason TEXT` 记录关闭原因，`braid issue reopen {number}` 重新打开 Issue。"
        ),
        member_login,
    )
}
pub(crate) fn pr_system_prompt(
    config: &Config,
    profile: &Profile,
    number: u64,
    head_ref: &str,
    member_login: Option<&str>,
) -> String {
    local_instructions(
        config,
        profile,
        &format!(
            "你正在处理 PR #{number}，当前分支是 {head_ref}。关联 Issue 提供需求、设计方案和验收依据；由你先承接实现计划、预演与关键未知的排障，再推进代码与验收，在当前独立工作区推进并向关联 Issue 交接结果。发现需求或设计问题时回到相关讨论澄清；已有代码需要承接和核验，不因接手而重复实现。将本地 commit push 到 origin 的 {head_ref}；草稿完成后可用 `braid pr ready {number}`，`braid pr merge {number}` 合并 origin 上当前发布的源分支。"
        ),
        member_login,
    )
}

pub(crate) fn render_event_references(claim: &TurnClaim) -> String {
    let label = if claim.work_item_kind == "pr" { "PR" } else { "Issue" };
    let mut output = format!(
        "请处理 {label} #{}。\n\n对象：{}#{}\n",
        claim.number, claim.repository, claim.number
    );
    if !claim.references.is_empty() {
        output.push_str("\n发生以下更新：\n");
        for reference in &claim.references {
            output.push_str("- ");
            output.push_str(reference);
            output.push('\n');
        }
    }
    output.push_str(&format!(
        "\n使用 `braid {} view {} --comments` 查看当前内容。\n",
        claim.work_item_kind, claim.number
    ));
    output
}

pub(crate) fn render_context_reset_notice(reset: &crate::store::ContextResetClaim) -> String {
    let label = if reset.work_item_kind == "pr" { "PR" } else { "Issue" };
    let mut message = format!(
        "你正在处理的 {label} #{} 有更新。当前会话结束后会用最新内容重新打开工作会话。\n\n更新：\n",
        reset.number,
    );
    for reference in &reset.references {
        message.push_str("- ");
        message.push_str(reference);
        message.push('\n');
    }
    message.push_str("请继续完成当前工作；如有尚未保存、后续需要接续的进展，可写到相关 Issue 或 PR。\n");
    message
}

pub(crate) fn enqueue_provider_blocked_status(
    store: &StoreActor,
    profile: &Profile,
    assignment_id: &str,
) -> Result<()> {
    if !profile.status_surfaces.is_empty() {
        store.enqueue_assignment_operational_status(
            assignment_id.into(),
            "> **本地运行状态**\n\n\
             **无法恢复执行**\n\n\
             当前工作已阻塞，系统没有启动替代执行。需要宿主修复或重新指派。"
                .into(),
        )?;
    }
    Ok(())
}
