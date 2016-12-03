(function ( $ ) {
jQuery(document).ready(function() {


    $('.showPop').click(function(){
        $('.pageInfo').fadeIn();
    });


    $('.hidePage').click(function(){
        $('.pageInfo').fadeOut();
    });


    function checkEmail(email) {

        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(email.trim());
    }

    function checkPhone(phone) {

        var re1 = /^1\d{10}$/;
        if (re1.test(phone.trim())) {
            return (true);
        }
        return (false);
    }

    $("#btnSubmit").click(function(){
        if ($(this).hasClass("busy"))
            return;

        $('#name').removeClass('error');
        $('#company').removeClass('error');
        $('#phone').removeClass('error');
        $('#email').removeClass('error');


        var errorMsg = "";
        var isError = false;

        if(!$('#name').val().trim()){
            $('#name').addClass('error');
            errorMsg = errorMsg || "请输入姓名";
            isError = true;
        }

        if(!$('#company').val().trim()){
            $('#company').addClass('error');
            errorMsg = errorMsg || "请输入公司名称";
            isError = true;
        }

        if(!$('#phone').val().trim()){
            $('#phone').addClass('error');
            errorMsg = errorMsg || "请输入手机号";
            isError = true;
        }

        if(!checkPhone($('#phone').val())){
            $('#phone').addClass('error');
            errorMsg = errorMsg || "请输入正确的手机格式";
            isError = true;
        }

        if (!$('#email').val().trim()){
            $('#email').addClass('error');
            errorMsg = errorMsg || "请输入邮箱";
            isError = true;
        }

        if(!checkEmail($('#email').val())){
            $('#email').addClass('error');
            errorMsg = errorMsg || "请输入正确的邮箱格式";
            isError = true;
        }

        var dataPost = {
            name: $('#name').val().trim(),
            company: $('#company').val().trim(),
            phone: $('#phone').val().trim(),
            email: $('#email').val().trim()
        };

        console.log(dataPost);

        $('.errorMsg').html(errorMsg);

        if(isError)
            return;

        $(this).addClass("busy");
        $(this).html("正在提交...");
        $(this).closest('form').submit();
    });



});






}( jQuery ));


var _vds = _vds || [];
window._vds = _vds;
(function(){
_vds.push(['setAccountId', '38018b3460394e43864ceb98019c901b']);
(function() {
  var vds = document.createElement('script');
  vds.type='text/javascript';
  vds.async = true;
  vds.src = ('https:' == document.location.protocol ? 'https://' : 'http://') + 'dn-growing.qbox.me/vds.js';
  var s = document.getElementsByTagName('script')[0];
  s.parentNode.insertBefore(vds, s);
})();
})();