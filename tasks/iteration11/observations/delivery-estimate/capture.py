import sqlite3,json,pathlib,datetime
base=pathlib.Path('/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs')
for task,ident,stamp in [('github','7fe42a1248f9d8','1202e245'),('sheet','3b5e3eeaa3b062','811f18d4')]:
 root=base/f'pi-braid--hackathon--{task}-{ident}'/'workspace/official-generation/template/.factory26'/f'20260929-042409-{stamp}'/'braid-state'
 c=sqlite3.connect(f'file:{root}/braid.sqlite3?mode=ro',uri=True);c.row_factory=sqlite3.Row
 items=[dict(r) for r in c.execute('select w.kind,w.number,w.state,l.title,l.body,l.head_ref,l.base_ref,l.desired_member_login from work_items w join local_items l using(node_id) order by w.number')]
 comments=[dict(r) for r in c.execute('select w.kind,w.number,c.comment_id,c.body,c.created_at,c.lifecycle from local_comments c join work_items w on w.node_id=c.work_item_node_id where c.comment_id in (select c2.comment_id from local_comments c2 where c2.work_item_node_id=c.work_item_node_id order by c2.comment_id desc limit 5) order by c.comment_id')]
 print(json.dumps(dict(task=task,captured=datetime.datetime.now(datetime.timezone.utc).isoformat(),status=json.loads((root/'status.json').read_text()),items=items,comments=comments),ensure_ascii=False))
