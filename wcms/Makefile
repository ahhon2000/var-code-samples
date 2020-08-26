.PHONY: install clean

DIR_DST_LOCAL = /var/www/ooocd/

install:
	rsync -ra --exclude-from=.rsync_exclusions wcms $(DIR_DST_LOCAL)
	#rsync style.css index.php $(DIR_DST_LOCAL)
clean:
	rm -rf $(DIR_DST_LOCAL)/*
