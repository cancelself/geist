import { serve } from "./deps.ts";

const port = 8000;

console.log(`HTTP webserver running. Access it at: http://localhost:${port}/`);

async function transform(request: Request): Promise<Response> {
    return new Response("Hello World\n");
}

serve(transform, { port });