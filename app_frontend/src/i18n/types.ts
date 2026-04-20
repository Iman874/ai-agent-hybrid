export type Language = "id" | "en";
export type TranslationKey = keyof typeof import("./locales/id").default;
