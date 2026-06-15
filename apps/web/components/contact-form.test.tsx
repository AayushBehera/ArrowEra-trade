import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ContactForm } from "./contact-form";

vi.mock("../lib/api", () => ({ api: { submitContact: vi.fn().mockResolvedValue({ id: "1", status: "received" }) } }));

describe("ContactForm", () => {
  it("rejects invalid input", async () => {
    render(<ContactForm />);
    fireEvent.submit(screen.getByRole("button").closest("form")!);
    expect(await screen.findByText(/check the form/i)).toBeInTheDocument();
  });
});
