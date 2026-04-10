### This chapter is special

Here I tried out their final option to store data in redis for get operation,
which is actually most faster one among all options.

But as redis is universal, you just have to make a fixture to keep the
test more like, `test_views.py` isolated.

So I implemented `clean_redis` fixture in `conftest` file.
