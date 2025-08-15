import asyncio
import os
import re
import json
import base64

from fastmcp import Client

# Test the MCP server using streamable-http transport.
# Use "/sse" endpoint if using sse transport.

#mcp_url = "http://localhost:8080/mcp/"
mcp_url = "https://mcp.tweekit.io/mcp/"

async def test_server():

    async with Client(mcp_url) as client:
        # List available resources
        resources = await client.list_resources()
        for resource in resources:
            print(f">>> 📦  Resource found: {resource.name}")

        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")

        successes = 0
        passed = False

        # Call the version resource (no parameters)
        try:
            version = await client.read_resource("config://tweekit-version")

            # Normalize the returned value to a string.
            content = version[0] if isinstance(version, (list, tuple)) and version else version
            ver_str = getattr(content, "text", content)
            ver_str = str(ver_str)

            print(f">>> 🔖 TweekIT API version: {ver_str}")
            # Assert the version matches the pattern ^\d+\.\d+\.\d+\.\d+$
            assert re.match(r"^\d+\.\d+\.\d+\.\d+$", ver_str), f"Unexpected version format: {ver_str!r}."
            successes += 1
        except Exception as e:
            print(f">>> ⚠️ Failed to call version resource: {e}")

        # Call the doctype tool with parameters, including apikey and apisecret from environment variables
        try:
            params = {
                "apiKey": os.environ.get("TWEEKIT_APIKEY"),
                "apiSecret": os.environ.get("TWEEKIT_APISECRET"),
                "extension": "*"
            }
            doctype = await client.call_tool("doctype", params)
            try:
                json.loads(json.dumps(doctype.data))  # Ensure the response is valid JSON
                print(f">>> ✅ Doctype tool response is valid JSON")
                successes += 1
            except json.JSONDecodeError:
                assert False, f">>> ⚠️ Doctype tool response is not valid JSON."
        except Exception as e:
            print(f">>> ⚠️ Failed to call doctype tool: {e}")

        # Call the convert tool, sending it base-64 encoded .png or .jpg files found in the directory alongside this module.
        for filename in os.listdir(os.path.dirname(__file__)):
            if filename.endswith((".png", ".docx")):
                with open(os.path.join(os.path.dirname(__file__), filename), "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    ext = filename.split(".")[-1]
                    params = {
                        "apiKey": os.environ.get("TWEEKIT_APIKEY"),
                        "apiSecret": os.environ.get("TWEEKIT_APISECRET"),
                        "blob": encoded_string,
                        "inext": ext,
                        "outfmt": "webp",
                        "noRasterize": True # this is only looked at for text documents and pdf output, so OK to always set to true, even for images
                    }
                    if ext != "png":
                        params["outfmt"] = "pdf" # for text base docs, test returning its conversion to PDF
                    convert = await client.call_tool("convert", params)
                    if convert.content:
                        content = convert.content
                        print(f">>> 🔖 Convert tool returned content for {filename}")
                        part = content[0]
                        if part.type == "resource":
                            print(f">>> ✅ Convert tool for {filename} returned a valid resource object.")
                            if not passed:
                                successes += 1
                        elif part.type == "image":
                            print(f">>> ✅ Convert tool for {filename} returned a valid image object.")
                            if not passed:
                                successes += 1
                        elif part.type == "text":
                            print(f">>> ⚠️  Convert tool rejected request: {part.text}")
                        else:
                            assert False, f">>> ⚠️ Unexpected content type for {filename}: Expected 'resource' or 'image', but got {part.type!r}."
                        if successes == 3:
                            passed = True
                    elif convert.data and "error" in convert.data:
                        print(f">>> ⚠️ Convert tool returned an error for {filename}: {convert.data['error']}")
                    else:
                        assert False, f">>> ⚠️ Convert tool for {filename} returned an unexpected response: data={convert.data}, content={convert.content}"

        if passed:
            print(f"PASSED")
        else:
            print(f"FAILED")

if __name__ == "__main__":
    asyncio.run(test_server())
