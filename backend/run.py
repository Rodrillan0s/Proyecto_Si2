from app import create_app
from gevent import monkey

monkey.patch_all()

app=create_app()

if __name__ == '__main__':
    #app.run(debug=True)  CAMBIAMOS app.run -> socketio.run
    app.socketio.run(app, host='127.0.0.1', port=5000, debug=True)