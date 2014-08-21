all: static/js/quenb-all.js static/js/quenb-all.min.js 

static/js/quenb-all.js: static/js/jquery-1.9.1.min.js static/js/noty/jquery.noty.min.js static/js/noty/layouts/all.min.js static/js/noty/themes/default.min.js static/js/quenb.js
	cat static/js/jquery-1.9.1.min.js static/js/noty/jquery.noty.min.js static/js/noty/layouts/all.min.js static/js/noty/themes/default.min.js static/js/quenb.js > static/js/quenb-all.js

static/js/quenb-all.min.js: static/js/jquery-1.9.1.min.js static/js/noty/jquery.noty.min.js static/js/noty/layouts/all.min.js static/js/noty/themes/default.min.js static/js/quenb.min.js
	cat static/js/jquery-1.9.1.min.js static/js/noty/jquery.noty.min.js static/js/noty/layouts/all.min.js static/js/noty/themes/default.min.js static/js/quenb.min.js > static/js/quenb-all.min.js

static/js/noty/jquery.noty.min.js: static/js/noty/jquery.noty.js
	slimit -m static/js/noty/jquery.noty.js > static/js/noty/jquery.noty.min.js

static/js/noty/layouts/all.min.js: static/js/noty/layouts/all.js
	slimit -m static/js/noty/layouts/all.js > static/js/noty/layouts/all.min.js

static/js/noty/themes/default.min.js: static/js/noty/themes/default.js
	slimit -m static/js/noty/themes/default.js > static/js/noty/themes/default.min.js

static/js/quenb.min.js: static/js/quenb.js
	slimit -m static/js/quenb.js > static/js/quenb.min.js

