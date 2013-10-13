from spindocker import app

import os

if os.environ['ENVIRONMENT'] == 'production':
    app.run()
else:
    app.run(debug=True, host='0.0.0.0', port=80)
