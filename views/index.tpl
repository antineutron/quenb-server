<html>
  <head><title>QuenB backend interface</title></head>
  <body>
    <script src='http://code.jquery.com/jquery-1.9.1.js'></script>
    <script src='http://code.jquery.com/ui/1.10.3/jquery-ui.js'></script>
    <link rel='stylesheet' href='http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css'>
    <link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap.min.css">
    <script src="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/js/bootstrap.min.js"></script>
 
    <div class="navbar navbar-inverse navbar-fixed-top" role="navigation">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
            <span class="sr-only">Toggle navigation</span>
          </button>
          <a class="navbar-brand" href="#">QuenB Signage System</a>
        </div>
        <div class="navbar-collapse collapse">
          <form class="navbar-form navbar-right" method='POST' action='/login'>
            <div class="form-group">
              <input name='username' type="text" placeholder="Username" class="form-control">
            </div>
            <div class="form-group">
              <input name='password' type="password" placeholder="Password" class="form-control">
            </div>
            <button type="submit" class="btn btn-success">Sign in</button>
          </form>
        </div><!--/.navbar-collapse -->
      </div>
    </div>
 
    <div class="jumbotron">
      <div class="container">
        <h1>Welcome to QuenB!</h1>
        <p>This is a digital signage system designed for use with the Raspberry Pi single-board computer. To administer the system, please log in.</p>
      </div>
    </div>
 
    <div>
    </div>
 
    <footer>
      <p>Original system code by Jack Edge</p>
      <p>Web interface (and some tidying up) by Andy Newton</p>
      <p>Like almost everything else, this site uses Bootstrap to make it look like Twitter for no good reason.</p>
    </footer>
 
  </body>
</html>

