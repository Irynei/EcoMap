app.controller('UserProfileCtrl', ['$scope', '$state', '$cookies', '$http', 'toaster', 'Upload', '$timeout',
  function($scope, $state, $cookies, $http, toaster, Upload, $timeout) {

    $scope.user = {};
    $scope.user.id = $cookies.get("id");

    $scope.tabs = [
      { heading: "Профіль користувача", route:"user_profile.info", active:false },
      { heading: "Мої проблеми", route:"user_profile.problems", active:false },
      { heading: "Мої коментарі", route:"user_profile.comments", active:false },
      { heading: "Редагування F.A.Q.", route:"user_profile.faq", active:false }
    ];

    $scope.$on("$stateChangeSuccess", function() {
      $scope.tabs.forEach(function(tab) {
        tab.active = $scope.active(tab.route);
      });
    });

    $scope.go = function(route){
      $state.go(route);
    };

    $scope.active = function(route){
      return $state.is(route);
    };

    if ($scope.user.id) {
      $http({
        url: '/api/user_detailed_info/' + $scope.user.id,
        method: 'GET'
      }).success(function(response) {
        $scope.user.data = response;
        $scope.user.data.avatar = $scope.user.data.avatar || 'http://placehold.it/200x200';
      });
    }

    $scope.password = {
      old_pass: "",
      new_pass: "",
      new_pass_confirm: ""
    };
    // $scope.changePassword = function(passwd) {
    //   console.log(passwd);
    //   if(!passwd.old_pass || !passwd.new_pass || !passwd.new_pass_confirm){
    //     return;
    //   }

    //   var data = {};
    //   data.id = $cookies.get('id');
    //   data.old_pass = passwd.old_pass;
    //   data.password = passwd.new_pass;
    //   console.log(data);
    //   $http({
    //     method: 'POST',
    //     url: '/api/change_password',
    //     data: {
    //       'id':data.id,
    //       'old_pass':data.old_pass,
    //       'password': data.new_pass
    //     }
    //   }).then(function successCallback(responce) {
    //     passwd = {};
    //     toaster.pop('success', 'Пароль', 'Пароль було успішно змінено!');
    //     $scope.changePasswordForm.$setUntouched();
    //   }, function errorCallback(responce) {
    //     if (responce.status == 401) {
    //       $scope.wrongOldPass = true;
    //     }
    //   });
    // };

    $scope.changePassword = function(){
    var data = {};
    data.id = $cookies.get('id');
    data.old_pass = $scope.password.old_pass;
    data.password = $scope.password.new_pass;
    console.log(data);
    $http({
        method: 'POST',
        url: '/api/change_password',
        data: data
    }).then(function successCallback(responce){
        $scope.password = {};
        toaster.pop('success', 'Пароль', 'Пароль було успішно змінено!');
        $scope.changePasswordForm.$setUntouched();
    },
      function errorCallback(responce){
        if(responce.status == 401) {
          $scope.wrongOldPass = true;
        };
        if(responce.status == 400) {
          toaster.pop('error', 'Пароль', 'Пароль не було змінено!')
        };
      });
    };

    $scope.redirect = function(state){
      $state.go(state);
    };

    $scope.wrongOldPass = false;
    $scope.getWrongPass = function() {
      return $scope.wrongOldPass;
    };

    $scope.changeWrongPass = function() {
      $scope.wrongOldPass = false;
    };
}]);
