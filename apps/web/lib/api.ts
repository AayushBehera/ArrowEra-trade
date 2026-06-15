import { ArrowEraClient } from "@arrowera/sdk";

export const api = new ArrowEraClient(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
);
