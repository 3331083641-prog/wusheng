import { create } from "zustand";
import { api } from "./api";
import { demo } from "./demo";
import type { Snapshot } from "./types";
interface State {
  data: Snapshot | null;
  loading: boolean;
  error: string;
  toast: string;
  refresh: () => Promise<void>;
  notify: (message: string) => void;
}
export const useStore = create<State>((set) => ({
  data: null,
  loading: true,
  error: "",
  toast: "",
  refresh: async () => {
    try {
      const data = location.search.includes("uiDemo=1") ? demo : await api<Snapshot>("/snapshot");
      set({ data, loading: false, error: "" });
    } catch (e) {
      set({
        loading: false,
        error: e instanceof Error ? e.message : "读取失败",
      });
    }
  },
  notify: (toast) => {
    set({ toast });
    window.setTimeout(() => set({ toast: "" }), 3500);
  },
}));
