 % include head.tpl current_user=current_user
    <div class="jumbotron">
      <div class="container">
        <h1>Welcome to QuenB!</h1>
        <p>Use this interface to set rules and actions for your signage displays.</p>
      </div>
    </div>
 
    <div class="center">
	  <h2>Recently-seen client displays</h2>
	  <table id='clientTable'>
	    <thead>
	      <tr><th>Client ID</th><th>Hostname</th><th>IP</th><th>MAC</th><th>Version</th><th>Actions</th></tr>
	    </thead>

	    <tbody>
	    % for client in clients:
		<tr>
		  <td>{{client.get('cid')}}</td>
		  <td>{{client.get('hostname')}}</td>
		  <td>{{client.get('ip')}}</td>
		  <td>{{client.get('mac')}}</td>
		  <td>{{client.get('version')}}</td>
		  <td>
		    Restart client
			Block client
			Create client rule
		  </td>
		</tr>
		% end
	    </tbody>
	    <tfoot>
	      <tr><th>Client ID</th><th>Hostname</th><th>IP</th><th>MAC</th><th>Version</th><th>Actions</th></tr>
	    </tfoot>
	  </table>
	  <script>
	    $(document).ready(function() {
            var oTable = $('#clientTable').dataTable();
        } );
	  </script>
    </div>
 
 % include tail.tpl
