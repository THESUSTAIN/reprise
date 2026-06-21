import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SidePanel from "./SidePanel";
import { PANEL } from "@fm/constants/testIds";
import { tasksApi, integrationsApi } from "@fm/lib/api";
import {
  ListChecks, FolderOpen, ChevronRight, ExternalLink, Plus,
  Cloud, HardDrive, Loader2, Link2,
} from "lucide-react";

export default function EspacePanel({ open, onClose }) {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [newTask, setNewTask] = useState("");

  const [driveStatus, setDriveStatus] = useState({ connected: false });
  const [driveFiles, setDriveFiles] = useState([]);
  const [oneStatus, setOneStatus] = useState({ connected: false });
  const [oneFiles, setOneFiles] = useState([]);
  const [docsLoading, setDocsLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    (async () => {
      setTasksLoading(true);
      setDocsLoading(true);
      try {
        const t = await tasksApi.list();
        if (!cancelled) setTasks(t.items || []);
      } catch {
        /* ignore */
      }
      if (!cancelled) setTasksLoading(false);

      const [g, m] = await Promise.allSettled([
        integrationsApi.google.status(),
        integrationsApi.microsoft.status(),
      ]);
      const gs = g.status === "fulfilled" ? g.value : { connected: false };
      const ms = m.status === "fulfilled" ? m.value : { connected: false };
      if (cancelled) return;
      setDriveStatus(gs);
      setOneStatus(ms);
      try {
        if (gs.connected) {
          const d = await integrationsApi.google.files(5);
          if (!cancelled) setDriveFiles(d.files || []);
        }
        if (ms.connected) {
          const d = await integrationsApi.microsoft.files(5);
          if (!cancelled) setOneFiles(d.files || []);
        }
      } catch {
        /* ignore */
      }
      if (!cancelled) setDocsLoading(false);
    })();
    return () => { cancelled = true; };
  }, [open]);

  const addTask = async () => {
    const title = newTask.trim();
    if (!title) return;
    try {
      const t = await tasksApi.create({ label: title });
      setTasks((prev) => [t, ...prev]);
      setNewTask("");
    } catch {
      /* ignore */
    }
  };

  const toggleTask = async (task) => {
    try {
      const updated = await tasksApi.patch(task.id, { done: !task.done });
      setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)));
    } catch {
      /* ignore */
    }
  };

  return (
    <SidePanel
      open={open}
      onClose={onClose}
      title="Mon espace de travail"
      subtitle="Tâches & documents synchronisés."
      width={460}
      testId={PANEL.espace}
      closeTestId={PANEL.espaceClose}
    >
      <div className="p-7 space-y-7">
        {/* Tasks */}
        <Section icon={ListChecks} title="Tâches du jour" badge={tasks.filter((t) => !t.done).length}>
          <div className="flex items-center gap-2 mb-3">
            <input
              data-testid="espace-new-task-input"
              type="text"
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addTask()}
              placeholder="Nouvelle tâche…"
              className="flex-1 px-3 h-9 rounded-xl bg-white border border-sand-300 text-[13.5px] focus:outline-none focus:border-navy/50"
            />
            <button
              data-testid="espace-add-task"
              onClick={addTask}
              className="w-9 h-9 grid place-items-center rounded-xl bg-navy text-cream hover:bg-navy-bright transition-colors"
            >
              <Plus size={14} />
            </button>
          </div>
          {tasksLoading ? (
            <p className="text-[13px] text-slate-500 inline-flex items-center gap-2">
              <Loader2 size={13} className="animate-spin" /> Chargement…
            </p>
          ) : tasks.length === 0 ? (
            <p className="text-[13px] text-slate-500">Aucune tâche. Ajoutez-en une !</p>
          ) : (
            <ul className="space-y-2" data-testid="espace-tasks-list">
              {tasks.slice(0, 8).map((t) => (
                <li
                  key={t.id}
                  className="flex items-center justify-between gap-3 p-3 rounded-2xl bg-white hover:bg-sand-100 transition-colors"
                >
                  <button
                    data-testid={`espace-task-toggle-${t.id}`}
                    onClick={() => toggleTask(t)}
                    className={`w-4 h-4 rounded border-2 shrink-0 transition-colors ${
                      t.done ? "bg-navy border-navy" : "border-slate-400 hover:border-navy"
                    }`}
                  />
                  <span className={`flex-1 text-[13.5px] ${t.done ? "line-through text-slate-400" : "text-slate-800"}`}>
                    {t.label}
                  </span>
                  {t.time && (
                    <span className="text-[11.5px] tabular-nums text-slate-500 font-medium">{t.time}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Section>

        {/* Documents from Drive + OneDrive */}
        <Section icon={FolderOpen} title="Documents récents">
          {docsLoading ? (
            <p className="text-[13px] text-slate-500 inline-flex items-center gap-2">
              <Loader2 size={13} className="animate-spin" /> Synchronisation…
            </p>
          ) : !driveStatus.connected && !oneStatus.connected ? (
            <div className="p-4 rounded-2xl bg-white border border-dashed border-sand-300 text-center">
              <p className="text-[13px] text-slate-600">Aucun stockage cloud branché.</p>
              <button
                data-testid="espace-connect-cloud"
                onClick={() => { onClose(); navigate("/integrations"); }}
                className="mt-3 inline-flex items-center gap-2 px-4 h-9 rounded-full bg-navy text-cream text-[12.5px] font-semibold hover:bg-navy-bright transition-colors"
              >
                <Link2 size={13} /> Brancher Google / OneDrive
              </button>
            </div>
          ) : (
            <ul className="space-y-2" data-testid="espace-docs-list">
              {driveFiles.map((f) => (
                <DocItem key={`g-${f.id}`} icon={HardDrive} name={f.name} link={f.web_view_link} />
              ))}
              {oneFiles.map((f) => (
                <DocItem key={`m-${f.id}`} icon={Cloud} name={f.name} link={f.web_url} />
              ))}
              {driveFiles.length === 0 && oneFiles.length === 0 && (
                <p className="text-[13px] text-slate-500">Aucun document récent.</p>
              )}
            </ul>
          )}
        </Section>
      </div>
    </SidePanel>
  );
}

function DocItem({ icon: Icon, name, link }) {
  return (
    <li className="flex items-center gap-3 p-3 rounded-2xl bg-white hover:bg-sand-100 transition-colors">
      <Icon size={14} className="text-navy shrink-0" />
      <span className="flex-1 text-[13.5px] text-slate-700 truncate">{name}</span>
      {link ? (
        <a href={link} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-navy">
          <ExternalLink size={13} />
        </a>
      ) : (
        <ChevronRight size={14} className="text-slate-400" />
      )}
    </li>
  );
}

function Section({ icon: Icon, title, badge, children }) {
  return (
    <section>
      <div className="flex items-center gap-2.5 mb-3">
        <span className="w-8 h-8 rounded-full bg-sand-200/70 grid place-items-center text-navy">
          <Icon size={14} strokeWidth={1.9} />
        </span>
        <h4 className="text-[14px] font-semibold text-slate-900">{title}</h4>
        {badge != null && (
          <span className="ml-auto text-[11px] font-semibold text-slate-500 bg-sand-100 px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </div>
      {children}
    </section>
  );
}
