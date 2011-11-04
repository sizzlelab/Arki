
# Get Django
wget --no-check-certificate http://www.djangoproject.com/download/1.3.1/tarball/ -O django.tgz

# Extract django directory
tar zxfv django.tgz Django-1.3.1/django

# Move it to the current directory
mv Django-1.3.1/django .

# Remove obsolete directory
rmdir Django-1.3.1

# Start dev server
python manage.py runserver

echo Next time you can start dev server by issuing command below:
echo python manage.py runserver

