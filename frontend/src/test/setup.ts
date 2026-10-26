/**
 * Setup bersama Vitest untuk matcher DOM dan isolasi render React antar-test.
 * afterEach(cleanup) mencegah elemen test lama memengaruhi query/accessibility test berikutnya.
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(cleanup);
