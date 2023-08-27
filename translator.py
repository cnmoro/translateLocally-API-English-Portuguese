import asyncio, itertools, struct, json
from pathlib import Path
from pprint import pprint

class Client:
    def __init__(self, *args):
        self.serial = itertools.count(1)
        self.futures = {}
        self.args = args

    async def initialize(self):
        self.proc = await asyncio.create_subprocess_exec(*self.args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self.read_task = asyncio.create_task(self.reader())
        
    async def terminate(self):
        self.proc.stdin.close()
        await self.proc.wait()

    async def __aenter__(self):
        self.proc = await asyncio.create_subprocess_exec(*self.args, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self.read_task = asyncio.create_task(self.reader())
        return self

    async def __aexit__(self, *args):
        self.proc.stdin.close()
        await self.proc.wait()

    def request(self, command, data, *, update=lambda data: None):
        message_id = next(self.serial)
        message = json.dumps({"command": command, "id": message_id, "data": data}).encode()
        future = asyncio.get_running_loop().create_future()
        self.futures[message_id] = future, update
        self.proc.stdin.write(struct.pack("@I", len(message)))
        self.proc.stdin.write(message)
        return future

    async def reader(self):
        while True:
            try:
                raw_length = await self.proc.stdout.readexactly(4)
                length = struct.unpack("@I", raw_length)[0]
                raw_message = await self.proc.stdout.readexactly(length)
                message = json.loads(raw_message)
                
                if not "id" in message:
                    continue

                future, update = self.futures[message["id"]]
                
                if "success" in message:
                    del self.futures[message["id"]]
                    if message["success"]:
                        future.set_result(message["data"])
                    else:
                        future.set_exception(Exception(message["error"]))
                elif "update" in message:
                    update(message["data"])
            except asyncio.IncompleteReadError:
                break
            except asyncio.CancelledError:
                break

class TranslateLocally(Client):
    async def list_models(self, *, include_remote=False):
        return await self.request("ListModels", {"includeRemote": bool(include_remote)})

    async def translate(self, text, src=None, trg=None, *, model=None, pivot=None, html=False):
        if src and trg:
            if model or pivot:
                raise Exception("Cannot combine src + trg and model + pivot arguments")
            spec = {"src": str(src), "trg": str(trg)}
        elif model:
            if pivot:
                spec = {"model": str(model), "pivot": str(pivot)}
            else:
                spec = {"model": str(model)}
        else:
            raise Exception("Missing src + trg or model argument")

        result = await self.request("Translate", {**spec, "text": str(text), "html": bool(html)})
        return result["target"]["text"]

    async def download_model(self, model_id, *, update=lambda data: None):
        return await self.request("DownloadModel", {"modelID": str(model_id)}, update=update)

def first(iterable, *default):
    return next(iter(iterable), *default) # passing as rest argument so it can be nothing and trigger StopIteration exception

async def get_build():
    paths = [
        Path("/usr/bin/translateLocally"),
        Path(__file__).resolve().parent / Path("../build/translateLocally")
    ]

    for path in paths:
        if path.exists():
            return TranslateLocally(path.resolve(), "-p")
    raise RuntimeError("Could not find translateLocally binary")

async def test_translation():
    async with get_build() as tl:
        models = await tl.list_models(include_remote=True)
        necessary_models = {("en", "pt"), ("pt", "en")}
        selected_models = {
            (src,trg): first(sorted(
                (
                    model
                    for model in models
                    if src in model["srcTags"] and trg == model["trgTag"]
                ),
                key=lambda model: 0 if model["type"] == "tiny" else 1
            ))
            for src, trg in necessary_models
        }

        pprint(selected_models)

        models = await tl.list_models(include_remote=True)
        assert all(
            model["local"]
            for selected_model in selected_models.values()
            for model in models
            if model["id"] == selected_model["id"]
        )

        print(await tl.translate("Hello world!", "en", "pt"))
        print(await tl.translate("Vamos traduzir mais coisas!", "pt", "en"))
