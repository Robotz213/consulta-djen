from asyncio import WindowsProactorEventLoopPolicy

from consulta_djen import PublicacoesDJEN

if __name__ == "__main__":
    cnj = PublicacoesDJEN.initialize()

    # async def main():
    #     await cnj.queue()
    #     # Aguarda todas as tasks criadas por cnj.queue()
    #     tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    #     if tasks:
    #         await asyncio.gather(*tasks)
    loop = WindowsProactorEventLoopPolicy().new_event_loop()
    loop.run_until_complete(cnj.queue())
