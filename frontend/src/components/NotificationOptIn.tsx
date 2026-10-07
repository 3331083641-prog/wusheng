import { useState, useEffect } from "react";
import type { Reminder } from "../types";
const preference = "wusheng-notification-opt-in";
export default function NotificationOptIn({ reminders }: { reminders: Reminder[] }) {
  const [enabled, setEnabled] = useState(() => localStorage.getItem(preference) === "yes");
  const [error, setError] = useState("");
  useEffect(() => {
    if (!enabled || !("Notification" in window) || Notification.permission !== "granted") return;
    for (const r of reminders.filter((r) => r.status === "pending" && r.daysLeft <= 0)) {
      const key = `wusheng-notified:${r.id}:${r.dueDate}`;
      if (localStorage.getItem(key)) continue;
      new Notification("物生到期提醒", { body: r.title, tag: r.id });
      localStorage.setItem(key, "yes");
    }
  }, [enabled, reminders]);
  return (
    <>
      <button
        className="button secondary"
        onClick={async () => {
          if (enabled) {
            setEnabled(false);
            localStorage.removeItem(preference);
            return;
          }
          if (!("Notification" in window)) {
            setError("此浏览器不支持通知，请导出系统日历提醒");
            return;
          }
          try {
            const granted = await Notification.requestPermission();
            if (granted === "granted") {
              setEnabled(true);
              localStorage.setItem(preference, "yes");
            } else setError("通知未获授权，可使用系统日历提醒");
          } catch {
            setError("当前环境无法开启通知，请使用日历导出");
          }
        }}
      >
        {enabled ? "关闭浏览器提醒" : "开启浏览器提醒"}
      </button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
