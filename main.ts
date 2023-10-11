import { serve } from "./deps.ts";

const port = 8000;
const server = serve({ port });

console.log(`HTTP webserver running. Access it at: http://localhost:${port}/`);

for await (const request of server) {
    request.respond({ body: "Hello World\n" });
}