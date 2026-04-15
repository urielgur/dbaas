import type { FieldRendererProps } from "./types";

export function TextFieldRenderer({ value }: FieldRendererProps) {
  const text = value == null ? "—" : String(value);
  return <span className="text-sm text-gray-800">{text}</span>;
}
