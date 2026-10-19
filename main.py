from scr.server.game_server import Server, configure_logging

if __name__ == "__main__":
    configure_logging()
    Server().run()

# Use CTRL+C when running to stop server
