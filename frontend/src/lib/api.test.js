import { API, normalizeTask, normalizeCheckin, normalizeHabit } from "./api";

describe("contrats frontend V1", () => {
  test("normalise une tâche provenant des formats backend supportés", () => {
    expect(normalizeTask({ label: "Relancer", done: true, priority: "high" })).toMatchObject({
      titre: "Relancer",
      statut: "Terminé",
      priorite: "Haute",
    });
  });

  test("normalise un check-in énergie et humeur", () => {
    expect(normalizeCheckin({ energy: 4, mood: 5, created_at: "2026-08-22" })).toMatchObject({
      energie: 80,
      humeur: "En feu",
      date: "2026-08-22",
    });
  });

  test("normalise une habitude sans tableau invalide", () => {
    expect(normalizeHabit({ name: "Lecture", done_today: true, streak: "3" })).toMatchObject({
      nom: "Lecture",
      done: true,
      streak: 3,
    });
  });

  test("utilise le préfixe API attendu", () => {
    expect(API).toMatch(/\/api$/);
  });
});
