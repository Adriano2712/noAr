import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MonitorForm } from "./MonitorForm";

describe("MonitorForm", () => {
  it("submits the name and url and clears the fields", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<MonitorForm onCreate={onCreate} />);

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Meu site" } });
    fireEvent.change(screen.getByLabelText("URL"), { target: { value: "https://meusite.com" } });
    fireEvent.click(screen.getByRole("button", { name: /adicionar monitor/i }));

    await waitFor(() =>
      expect(onCreate).toHaveBeenCalledWith({ name: "Meu site", url: "https://meusite.com" })
    );
    await waitFor(() => expect(screen.getByLabelText("Nome")).toHaveValue(""));
  });

  it("shows an error message when creation fails", async () => {
    const onCreate = vi.fn().mockRejectedValue(new Error("URL inválida"));
    render(<MonitorForm onCreate={onCreate} />);

    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Meu site" } });
    fireEvent.change(screen.getByLabelText("URL"), { target: { value: "https://meusite.com" } });
    fireEvent.click(screen.getByRole("button", { name: /adicionar monitor/i }));

    expect(await screen.findByText("URL inválida")).toBeInTheDocument();
  });
});
