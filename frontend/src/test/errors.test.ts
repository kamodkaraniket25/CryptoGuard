import axios, { AxiosError, AxiosHeaders, type AxiosResponse } from "axios";
import { errorMessage } from "../services/api";

function httpError(status: number, data: unknown, code = "ERR_BAD_RESPONSE"): AxiosError {
  const response = {
    data,
    status,
    statusText: "",
    headers: {},
    config: { headers: new AxiosHeaders() },
  } as AxiosResponse;
  return new AxiosError("request failed", code, undefined, undefined, response);
}

describe("API error messages", () => {
  it("names a timeout separately from a stopped API", () => {
    const error = new AxiosError("timeout of 60000ms exceeded", "ECONNABORTED");
    expect(errorMessage(error)).toMatch(/timed out/i);
    expect(errorMessage(error)).not.toMatch(/OSV/);
  });

  it("tells the reader to start Uvicorn when there is no response", () => {
    const error = new AxiosError("Network Error", "ERR_NETWORK");
    expect(errorMessage(error)).toMatch(/Cannot reach the CryptoGuard backend/);
    expect(errorMessage(error)).toMatch(/port 8000/);
  });

  it("shows a database failure without calling the API offline", () => {
    expect(errorMessage(httpError(503, { detail: "Database is unavailable." }))).toBe("Database is unavailable.");
  });

  it("passes through an external source failure returned by the API", () => {
    const message = "OSV did not return a usable result for this query.";
    expect(errorMessage(httpError(502, { detail: message }))).toBe(message);
  });

  it("describes an HTTP client error when the API sent no detail", () => {
    expect(errorMessage(httpError(422, {}))).toMatch(/HTTP 422/);
  });

  it("ignores non-axios errors that are not Error instances", () => {
    expect(errorMessage("nope")).toBe("Something went wrong.");
    expect(axios.isAxiosError(httpError(500, { detail: "An unexpected error occurred." }))).toBe(true);
  });
});
