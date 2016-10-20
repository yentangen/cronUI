$(function() {
  $('#searchField').keyup(function() {
      var value = this.value.toLowerCase();

      $('#crontabTable').find("tr").each(function(index) {
          if (index < 1) {
            return;
          }

          var id = $(this).find("td").text().toLowerCase();
          $(this).toggle(id.indexOf(value) !== -1);
      });

      $('#jobTable').find("tr").each(function(index) {
          if (index < 1) {
            return;
          }

          var id = $(this).find("td").text().toLowerCase();
          $(this).toggle(id.indexOf(value) !== -1);
      });

      $('#sshKeysTable').find("tr").each(function(index) {
          if (index < 1) {
            return;
          }

          var id = $(this).find("td").text().toLowerCase();
          $(this).toggle(id.indexOf(value) !== -1);
      });
  });
});
