(function (bryn, $, undefined) {
  "use strict";

  var dashboard = bryn.dashboard || {};

  dashboard.hideSSHKeyFields = function (form) {
    form = $(form);
    form.find("input[name='server_key_name']").closest("div.form-group").hide();
    form.find("textarea[name='server_key']").closest("div.form-group").hide();
  };

  dashboard.showSSHKeyFields = function (form) {
    form = $(form);
    form.find("input[name='server_key_name']").closest("div.form-group").show();
    form.find("textarea[name='server_key']").closest("div.form-group").show();
  };

  dashboard.refreshInstances = function (container) {
    console.log("Refresh...");
    container = $(container);
    $.ajax({
      url: "/get_instances_table",
      type: "get",
      data: {team_id: container.attr("data-team-id")},

      success: function(json) {
        container.html(json.instances_table);
      }
    });
  };

  dashboard.refreshInstancesAfter = function (container, timeArray) {
    for (var i in timeArray) {
      console.log(timeArray[i]);
      setTimeout(dashboard.refreshInstances, timeArray[i], container);
    }
  };

  dashboard.refreshVolumes = function (container) {
    console.log("Refresh...");
    container = $(container);
    $.ajax({
      url: "/get_volumes_table",
      type: "get",
      data: {team_id: container.attr("data-team-id")},

      success: function(json) {
        container.html(json.volumes_table);
      }
    });
  };

  dashboard.refreshVolumesAfter = function (container, timeArray) {
    for (var i in timeArray) {
      console.log(timeArray[i]);
      setTimeout(dashboard.refreshVolumes, timeArray[i], container);
    }
  };

  dashboard.ajaxInstanceAction = function (event, url) {
    var target = $(event.target);
    var teamContainer = target.closest("div.team-container");
    var tableContainer = target.closest("div.instances-table-container");

    event.preventDefault();

    target.closest("ul").siblings(".dropdown-toggle").children("i:first-child").addClass("fa-spin fa-spinner");

    $.ajax({
      url: url,
      type: "get",

      complete: function(xhr) {
        var json = JSON.parse(xhr.responseText);
        var messages = teamContainer.find("div.messages-container");
        if ("messages_html" in json) {
          messages.empty();
          messages.html(json.messages_html);
        }
        messages.children().hide().fadeIn(500).delay(10000).fadeOut(500);
        dashboard.refreshInstancesAfter(tableContainer, [1000, 2000, 5000, 10000]);
      }
    });
  };

  bryn.dashboard = dashboard;

  /*
  Event handlers
  */

  // AJAX forms
  $(document).on('submit', 'form.launch-custom-form, form.launch-gvl-form', function(event){
    event.preventDefault();
    bryn.ajaxForms.formPOST(this, true, function (form) {
      var tableContainer = $(form).closest('.team-container').find('.instances-table-container');
      $('html, body').stop().animate({scrollTop: tableContainer.offset().top}, '500', 'swing');
      dashboard.refreshInstancesAfter(tableContainer, [2000, 5000, 10000]);
    });
  });

  // Instances refresh button
  $(document).on("click", "button[data-team-action='refresh-instances']", function(){
    var button = $(this);
    button.find("i").addClass("fa-spin fa-spinner");
    dashboard.refreshInstances(button.closest(".instances-table-container"));
  });

  // Volumes refresh button
  $(document).on("click", "button[data-team-action='refresh-volumes']", function(){
    var button = $(this);
    button.find("i").addClass("fa-spin fa-spinner");
    dashboard.refreshVolumes(button.closest(".volumes-table-container"));
  });

 // Instance actions
  $(document).on("click", "ul.instance-actions-list > li > a", function (event) {
    event.preventDefault();
    var anchor = $(this);
    var url = anchor.attr("href");
    dashboard.ajaxInstanceAction(event, url);
  });

  $(document).ready(function () {
    $('select option[value="cloudman"]').hide();
    // Initially hide SSH key fields (as required)
    $("form.launch-custom-form").each(function () {
      var form = $(this);
      if (form.find("select[name='server_key_name_choice']").val() != "bryn:new") {
        dashboard.hideSSHKeyFields(form);
      }
    });

    // SSH key fields how/hide on name change
    $("form.launch-custom-form select[name='server_key_name_choice']").change(function () {
      var keySelect = $(this);
      var form = keySelect.closest("form.launch-custom-form");

      if (keySelect.val() == "bryn:new") {
        dashboard.showSSHKeyFields(form);
      } else {
        dashboard.hideSSHKeyFields(form);
      }
    });
  });
  
})(window.bryn = window.bryn || {}, jQuery);
