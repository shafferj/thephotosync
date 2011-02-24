from pylons.util import PylonsInstaller

def prompt(text, default=None, type=str):
    if type == bool:
        text += " ["
        text += "Y" if default else "y"
        text += "/"
        text += "n" if default else "N"
        text += "]"
    elif type == str and default:
        text += " (%s)" % default
    text += ": "
    while True:
        r = raw_input(text)
        if type == bool:
            if r.lower() in ['n','no']:
                return False
            elif r.lower() in ['y', 'yes']:
                return True
            elif r:
                print "Invalid input"
            else:
                return default
        else:
            return r or default


class PhotosyncInstaller(PylonsInstaller):

    def config_content(self, command, vars):
        print "Please answer some questions about this deployment."
        print
        debug = prompt("Turn debug mode on?", default=True, type=bool)
        vars['debug'] = "true" if debug else "false"

        vars['fb_app_id'] = prompt("Facebook App Id")
        vars['fb_api_key'] = prompt("Facebook Api Key")
        vars['fb_app_secret'] = prompt("Facebook App Secret")
        vars['base_url'] = prompt("Base url of your site")
        vars['flickr_api_key'] = prompt("Flickr API key")
        vars['flickr_api_secret'] = prompt("Flickr API secret")

        vars['mysql_user'] = prompt("MySQL database user", default="root")
        vars['mysql_passwd'] = prompt("MySQL database password")
        vars['mysql_host'] = prompt("MySQL host", default="localhost")
        vars['mysql_port'] = prompt("MySQL port", default="3306")
        vars['mysql_db'] = prompt("MySQL database name", default="photosync")

        vars['smtp_server'] = prompt("SMTP server host", default="localhost")
        vars['error_email_from'] = prompt("Error email address",
                                          default="paste@localhost")
        vars['email_to'] = '' if debug else prompt("Send error emails to")

        vars['port'] = prompt("Run the server on port", default="8080")

        return super(PhotosyncInstaller, self).config_content(command, vars)
