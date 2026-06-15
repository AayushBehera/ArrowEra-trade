"use client";

import { FormEvent, useState } from "react";
import { z } from "zod";
import { Button, Card } from "@arrowera/ui";
import { api } from "../lib/api";

const schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  company: z.string().min(2),
  phone: z.string().optional(),
  message: z.string().min(10)
});

export function ContactForm() {
  const [status, setStatus] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const parsed = schema.safeParse(Object.fromEntries(form));
    if (!parsed.success) {
      setStatus("Check the form fields and try again.");
      return;
    }
    try {
      await api.submitContact(parsed.data);
      event.currentTarget.reset();
      setStatus("Message received and stored securely.");
    } catch (error) {
      setStatus(`Submission failed: ${(error as Error).message}`);
    }
  }
  return <Card><form className="form" onSubmit={submit}><input name="name" aria-label="Name" placeholder="Name" required/><input name="email" aria-label="Email" type="email" placeholder="Email" required/><input name="company" aria-label="Company" placeholder="Company" required/><input name="phone" aria-label="Phone" placeholder="Phone"/><textarea name="message" aria-label="Message" placeholder="What should the platform solve?" required/><Button>Send inquiry</Button>{status && <div className="status">{status}</div>}</form></Card>;
}
