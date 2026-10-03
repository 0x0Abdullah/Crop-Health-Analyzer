import json, logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from src.database.db import get_connection
from src.database.models import AnalysisRecord, ChatMessageRecord
logger=logging.getLogger("repository")
class DatabaseRepository:
    def __init__(self, db_path=None): self.db_path=db_path
    def _conn(self): return get_connection() if self.db_path is None else get_connection(self.db_path)
    def save_analysis(self, record: AnalysisRecord, evidence_items=None, plant_id=None, environment=None, evidence_level="Insufficient evidence", image_metadata=None):
        conn=self._conn()
        try:
            with conn:
                cur=conn.execute("INSERT INTO analyses (session_id,crop,input_mode,symptoms,has_image,result_condition,confidence,evidence_level,severity,report_json,plant_id,environment_json,model_version,knowledge_version,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(record.session_id,record.crop,record.input_mode,record.symptoms,int(record.has_image),record.result_condition,record.confidence,evidence_level,record.severity,record.report_json,plant_id,json.dumps(environment or {}),"heuristic-v1","local-kb",record.created_at))
                aid=cur.lastrowid
                for ev in evidence_items or []:
                    conn.execute("INSERT INTO evidence (analysis_id,source,title,content,url,created_at) VALUES (?,?,?,?,?,?)",(aid,ev.get("source","Agricultural Knowledge Record"),ev.get("title",""),ev.get("content") or ev.get("text",""),ev.get("url",""),record.created_at))
                for i,img in enumerate(image_metadata or []):
                    conn.execute("INSERT INTO analysis_images (analysis_id,image_index,filename,width,height,quality,sharpness,brightness) VALUES (?,?,?,?,?,?,?,?)",(aid,i,img.get("filename",""),img.get("width",0),img.get("height",0),img.get("quality","unknown"),img.get("sharpness_score"),img.get("brightness_score")))
            return aid
        except Exception as e:
            logger.error("Failed to save analysis: %s",e); return -1
        finally: conn.close()
    def get_analysis_history(self, limit=50, crop=None, plant_id=None, evidence_level=None):
        conn=self._conn()
        try:
            clauses=[]; args=[]
            if crop: clauses.append("crop=?"); args.append(crop)
            if plant_id: clauses.append("plant_id=?"); args.append(plant_id)
            if evidence_level: clauses.append("evidence_level=?"); args.append(evidence_level)
            where=(" WHERE "+" AND ".join(clauses)) if clauses else ""
            args.append(max(1,min(int(limit),500)))
            rows=conn.execute(f"SELECT id,session_id,crop,input_mode,symptoms,has_image,result_condition,confidence,evidence_level,severity,plant_id,created_at FROM analyses{where} ORDER BY id DESC LIMIT ?",args).fetchall()
            return [dict(r) for r in rows]
        finally: conn.close()
    def get_analysis_by_id(self, analysis_id):
        conn=self._conn()
        try:
            row=conn.execute("SELECT * FROM analyses WHERE id=?",(analysis_id,)).fetchone()
            if not row:return None
            d=dict(row); d["evidence"]=[dict(r) for r in conn.execute("SELECT source,title,content,url FROM evidence WHERE analysis_id=?",(analysis_id,)).fetchall()]; d["images"]=[dict(r) for r in conn.execute("SELECT * FROM analysis_images WHERE analysis_id=? ORDER BY image_index",(analysis_id,)).fetchall()]; return d
        finally: conn.close()
    def save_chat_message(self, record):
        conn=self._conn()
        try:
            aid=record.analysis_id if record.analysis_id and record.analysis_id>0 else None
            with conn:
                cur=conn.execute("INSERT INTO messages (analysis_id,session_id,role,message,created_at) VALUES (?,?,?,?,?)",(aid,record.session_id,record.role,record.message,record.created_at)); return cur.lastrowid
        finally: conn.close()
    def get_chat_messages(self, session_id):
        conn=self._conn()
        try:return [dict(r) for r in conn.execute("SELECT id,analysis_id,session_id,role,message,created_at FROM messages WHERE session_id=? ORDER BY id",(session_id,)).fetchall()]
        finally:conn.close()
    def create_plant(self, name, crop, variety="", planting_date="", location="", growing_environment="", notes=""):
        conn=self._conn(); now=datetime.now().isoformat()
        try:
            with conn:
                cur=conn.execute("INSERT INTO plants(name,crop,variety,planting_date,location,growing_environment,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",(name,crop,variety,planting_date,location,growing_environment,notes,now)); return cur.lastrowid
        finally:conn.close()
    def get_plants(self):
        conn=self._conn()
        try:return [dict(r) for r in conn.execute("SELECT * FROM plants ORDER BY id DESC").fetchall()]
        finally:conn.close()
    def get_plant(self, plant_id):
        conn=self._conn()
        try:
            r=conn.execute("SELECT * FROM plants WHERE id=?",(plant_id,)).fetchone(); return dict(r) if r else None
        finally:conn.close()
    def get_plant_timeline(self, plant_id):
        conn=self._conn()
        try:return [dict(r) for r in conn.execute("SELECT id,created_at,result_condition,evidence_level,severity FROM analyses WHERE plant_id=? ORDER BY created_at",(plant_id,)).fetchall()]
        finally:conn.close()

    def create_reminder(self, plant_id, due_date, note):
        conn=self._conn()
        try:
            with conn:
                cur=conn.execute("INSERT INTO reminders(plant_id,due_date,note) VALUES(?,?,?)",(plant_id,due_date,note)); return cur.lastrowid
        finally: conn.close()
    def get_reminders(self, plant_id=None, include_completed=False):
        conn=self._conn()
        try:
            q="SELECT r.*, p.name AS plant_name, p.crop AS plant_crop FROM reminders r LEFT JOIN plants p ON p.id=r.plant_id"; args=[]; clauses=[]
            if plant_id: clauses.append("r.plant_id=?"); args.append(plant_id)
            if not include_completed: clauses.append("r.completed=0")
            if clauses:q+=" WHERE "+" AND ".join(clauses)
            q+=" ORDER BY r.due_date, r.id"
            return [dict(r) for r in conn.execute(q,args).fetchall()]
        finally: conn.close()
    def complete_reminder(self, reminder_id):
        conn=self._conn()
        try:
            with conn: conn.execute("UPDATE reminders SET completed=1 WHERE id=?",(reminder_id,))
        finally: conn.close()

    # ------------------------------------------------------------------ reminders (extra)
    def get_due_reminders(self, today=None):
        """Open reminders that are due today or overdue."""
        cutoff=(today or date.today()).isoformat()
        return [r for r in self.get_reminders() if str(r.get("due_date",""))<=cutoff]
    def delete_reminder(self, reminder_id):
        conn=self._conn()
        try:
            with conn: conn.execute("DELETE FROM reminders WHERE id=?",(reminder_id,))
        finally: conn.close()

    # ------------------------------------------------------------------ deletion
    def delete_analysis(self, analysis_id):
        conn=self._conn()
        try:
            with conn:
                for table in ("evidence","analysis_images","messages"):
                    conn.execute(f"DELETE FROM {table} WHERE analysis_id=?",(analysis_id,))
                conn.execute("DELETE FROM analyses WHERE id=?",(analysis_id,))
        finally: conn.close()
    def delete_all_analyses(self):
        conn=self._conn()
        try:
            with conn:
                for table in ("evidence","analysis_images","messages","analyses"): conn.execute(f"DELETE FROM {table}")
        finally: conn.close()
    def delete_plant(self, plant_id):
        """Delete a plant and its reminders. Past assessments are kept but unlinked."""
        conn=self._conn()
        try:
            with conn:
                conn.execute("UPDATE analyses SET plant_id=NULL WHERE plant_id=?",(plant_id,))
                conn.execute("DELETE FROM reminders WHERE plant_id=?",(plant_id,))
                conn.execute("DELETE FROM plants WHERE id=?",(plant_id,))
        finally: conn.close()
    def delete_all_plants(self):
        conn=self._conn()
        try:
            with conn:
                conn.execute("UPDATE analyses SET plant_id=NULL")
                conn.execute("DELETE FROM reminders"); conn.execute("DELETE FROM plants")
        finally: conn.close()
    def delete_chat_messages(self, session_id=None):
        conn=self._conn()
        try:
            with conn:
                if session_id: conn.execute("DELETE FROM messages WHERE session_id=?",(session_id,))
                else: conn.execute("DELETE FROM messages")
        finally: conn.close()

    # ------------------------------------------------------------------ settings
    def get_settings(self):
        """Return all persisted settings as {key: python value}."""
        conn=self._conn()
        try:
            out={}
            for r in conn.execute("SELECT key,value FROM settings").fetchall():
                try: out[r["key"]]=json.loads(r["value"])
                except (TypeError, ValueError): continue
            return out
        finally: conn.close()
    def set_setting(self, key, value):
        conn=self._conn()
        try:
            with conn:
                conn.execute("INSERT INTO settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",(key,json.dumps(value),datetime.now().isoformat()))
        finally: conn.close()
    def set_settings(self, values):
        conn=self._conn(); now=datetime.now().isoformat()
        try:
            with conn:
                for k,v in values.items():
                    conn.execute("INSERT INTO settings(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",(k,json.dumps(v),now))
        finally: conn.close()
    def clear_settings(self):
        conn=self._conn()
        try:
            with conn: conn.execute("DELETE FROM settings")
        finally: conn.close()

    # ------------------------------------------------------------------ stats / export
    def get_counts(self):
        conn=self._conn()
        try:
            def n(sql): return int(conn.execute(sql).fetchone()[0])
            return {"assessments":n("SELECT COUNT(*) FROM analyses"),"plants":n("SELECT COUNT(*) FROM plants"),
                    "open_reminders":n("SELECT COUNT(*) FROM reminders WHERE completed=0"),"chat_messages":n("SELECT COUNT(*) FROM messages")}
        finally: conn.close()
    def export_all(self):
        """Complete JSON-serialisable backup of the user's data (never includes settings secrets or API keys)."""
        conn=self._conn()
        try:
            def rows(sql): return [dict(r) for r in conn.execute(sql).fetchall()]
            return {"exported_at":datetime.now().isoformat(),
                    "analyses":rows("SELECT * FROM analyses ORDER BY id"),
                    "evidence":rows("SELECT * FROM evidence ORDER BY id"),
                    "plants":rows("SELECT * FROM plants ORDER BY id"),
                    "reminders":rows("SELECT * FROM reminders ORDER BY id"),
                    "messages":rows("SELECT * FROM messages ORDER BY id")}
        finally: conn.close()
