import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge, Change, number } from "../src/components/ui";
describe("honest commercial presentation", () => {
  it("shows missing percentages as missing comparisons", () => {
    render(<Change value={null} />);
    expect(screen.getByText("No comparison")).toBeInTheDocument();
  });
  it("formats zero distinctly from missing data", () => {
    expect(number(null)).toBe("—");
    expect(number(0)).toBe("0");
  });
  it("distinguishes technical errors from critical business risk", () => {
    render(
      <>
        <Badge status="ERROR" />
        <Badge status="CRITICO" />
      </>,
    );
    expect(screen.getByText("Error")).toHaveClass("error");
    expect(screen.getByText("Critical")).toHaveClass("critico");
  });
});
