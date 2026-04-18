/**
 * FieldRegistry — maps renderer keys to React components.
 *
 * To add a new renderer:
 *   1. Create the component in this directory.
 *   2. Import and register it here.
 *   3. Reference the key in COLUMN_DEFINITIONS.
 */

import { ArgoCDLinksField } from "./ArgoCDLinksField";
import { ConnectField } from "./ConnectField";
import { DBTypeField } from "./DBTypeField";
import { LinkField } from "./LinkField";
import { NotesField } from "./NotesField";
import { TextFieldRenderer } from "./TextFieldRenderer";
import type { FieldRenderer } from "./types";

const registry: Record<string, FieldRenderer> = {
  text: TextFieldRenderer,
  link: LinkField,
  argoCDLinks: ArgoCDLinksField,
  dbType: DBTypeField,
  connect: ConnectField,
  notes: NotesField,
};

export function getRenderer(key: string): FieldRenderer {
  return registry[key] ?? TextFieldRenderer;
}
