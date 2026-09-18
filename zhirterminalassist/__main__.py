import sys
from zhirterminalassist.gui.app import create_application

def main():
    app, window = create_application()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
