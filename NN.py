import time
import numpy as np
import tensorflow as tf
import os
import tensorflow.contrib.slim as slim
import re
import sqlite3

# Hyper parameters
epochs = 10
batch_size = 5
keep_probability = .0001
learning_rate = 0.001

#file parameters
dataset_name = "two"
checkpoint_dir = "checkpoint"
database_path = "output_data_detected_ads.sqlite"

def conv_net(x, keep_prob, reuse):
    with tf.variable_scope("model", reuse=reuse):
    
        # 10
        full1 = tf.contrib.layers.fully_connected(inputs=x, num_outputs=128, activation_fn=tf.nn.relu)
        full1 = tf.nn.dropout(full1, keep_prob)
    
        # 11
        full2 = tf.contrib.layers.fully_connected(inputs=full1, num_outputs=256, activation_fn=tf.nn.relu)
        full2 = tf.nn.dropout(full2, keep_prob)
    
        # 12
        full3 = tf.contrib.layers.fully_connected(inputs=full2, num_outputs=512, activation_fn=tf.nn.relu)
        full3 = tf.nn.dropout(full3, keep_prob)
    
        # 13
        full4 = tf.contrib.layers.fully_connected(inputs=full3, num_outputs=1024, activation_fn=tf.nn.relu)
        full4 = tf.nn.dropout(full4, keep_prob)
        
        #14
        full5 = tf.contrib.layers.fully_connected(inputs=full4, num_outputs=1024, activation_fn=tf.nn.relu)
        full5 = tf.nn.dropout(full5, keep_prob)
    
        # 15
        out = tf.contrib.layers.fully_connected(inputs=full5, num_outputs=1, activation_fn=None)
        return out

def model_dir():
    return "{}_{}".format(
        dataset_name, batch_size)
    
def save(sess, step):
    model_name = "cifar10Normal.model"
    check_dir = os.path.join(checkpoint_dir, model_dir())
  
    if not os.path.exists(check_dir):
      os.makedirs(check_dir)
  
    saver.save(sess,
            os.path.join(check_dir, model_name),
            global_step=step)

def load(sess):
    print(" [*] Reading checkpoints...")
    check_dir = os.path.join(checkpoint_dir, model_dir())
    
    ckpt = tf.train.get_checkpoint_state(check_dir)
    if ckpt and ckpt.model_checkpoint_path:
      ckpt_name = os.path.basename(ckpt.model_checkpoint_path)
      saver.restore(sess, os.path.join(check_dir, ckpt_name))
      counter = int(next(re.finditer("(\d+)(?!.*\d)",ckpt_name)).group(0))
      print(" [*] Success to read {}".format(ckpt_name))
      return True, counter
    else:
      print(" [*] Failed to find a checkpoint")
      return False, 0
  
def show_all_variables():
    model_vars = tf.trainable_variables()
    slim.model_analyzer.analyze_vars(model_vars, print_info=True)
    
def loadData():
    with sqlite3.connect(database_path, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS prediction_table (\
            id INTEGER PRIMARY KEY AUTOINCREMENT,\
            url TEXT,\
            visit_id INTEGER,\
            trained TEXT,\
            knn_pred INTEGER,\
            nn_pred INTEGER);")
        cur.execute("SELECT A_one, A_two, B_one, B_two, C_one, C_two, D_one, D_two, F_script, F_resource, " + dataset_name + "_month_list FROM http_requests \
                    WHERE A_one IS NOT NULL AND A_two IS NOT NULL AND B_one IS NOT NULL AND B_two IS NOT NULL AND C_one IS NOT NULL AND\
                    C_two IS NOT NULL AND D_one IS NOT NULL AND D_two IS NOT NULL AND \
                    F_script IS NOT NULL AND F_resource IS NOT NULL")
        
        rows = cur.fetchall()
     
        x = []
        y = []
        for row in rows:
            data_row = []
            data_row.append(float(row[0]))
            data_row.append(float(row[1]))
            data_row.append(float(row[2]))
            data_row.append(float(row[3]))
            data_row.append(float(row[4]))
            data_row.append(float(row[5]))
            data_row.append(float(row[6]))
            data_row.append(float(row[7]))
            data_row.append(float(row[8]))
            data_row.append(float(row[9]))
            
            x.append(data_row)
            y.append([float(row[10])])
            
        
        database.commit()    
        return np.asarray(x), np.asarray(y)
            
def next_batch(num, data, labels):
    '''
    Return a total of `num` random samples and labels. 
    '''
    idx = np.arange(0 , len(data))
    np.random.shuffle(idx)
    idx = idx[:num]
    data_shuffle = [data[ i] for i in idx]
    labels_shuffle = [labels[ i] for i in idx]

    return np.asarray(data_shuffle), np.asarray(labels_shuffle)

# Tell TensorFlow that the model will be built into the default Graph.
with tf.Graph().as_default():
    
    # Inputs
    x = tf.placeholder(tf.float32, shape=(None, 10), name='input_x')
    y =  tf.placeholder(tf.float32, shape=(None, 1), name='output_y')
    keep_prob = tf.placeholder(tf.float32, name='keep_prob')
    
    #Load X and Y
    X, Y = loadData()
    
    print("Shape X: ", X.shape)
    print("Shape Y: ", Y.shape)
	
    #Split into training and validation set
    training_size = int(len(X) * .8)
    train_x = X[:training_size]
    train_y = Y[:training_size]
	
    valid_x = X[training_size:]
    valid_y = Y[training_size:]
    
    # Build model
    logits = conv_net(x, keep_prob, False)
    
    #Create saver
    saver = tf.train.Saver()
    
    # Loss and Optimizer
    cost = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=logits, labels=y))
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
    
    # Accuracy
    correct_pred = tf.equal(tf.argmax(logits, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32), name='accuracy')
    
    init_ops = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
    
    print('Training...')
    with tf.Session(config=tf.ConfigProto(log_device_placement=False)) as sess:
        # Initializing the variables
        sess.run(init_ops)
        
        best_accuracy = 0.0
        last_accuracy = 0.0
        best_epoch = 0
        total_time = 0.0
        counter = 1
        start_time = time.time()
        could_load, checkpoint_counter = load(sess)
        if could_load:
          counter = checkpoint_counter
          print(" [*] Load SUCCESS")
        else:
          print(" [!] Load failed...")
          
        for epoch in range(epochs):
            batch_x, batch_y = next_batch(batch_size, train_x, train_y)
            valid_batch_x, valid_batch_y = next_batch(batch_size, valid_x, valid_y)
              
            sess.run(optimizer,
							 feed_dict={
								 x: batch_x,
								 y: batch_y,
								 keep_prob: keep_probability
							 })
	  
            loss = sess.run(cost,
                        feed_dict={
								 x: batch_x,
								 y: batch_y,
								 keep_prob: 1.
							 })
	  
            valid_acc = sess.run(accuracy,
							 feed_dict={
								 x: valid_batch_x,
								 y: valid_batch_y,
								 keep_prob: 1.
							 })
        
            total_time = time.time() - start_time
            last_accuracy = valid_acc
            print('Epoch: [%2d/%2d] time: %4.4f Loss: %4f Validation Accuracy: %4f' \
                  % (epoch + 1, epochs, total_time, loss, valid_acc))
            
            if best_accuracy < valid_acc:
                best_accuracy = valid_acc
                best_epoch = epoch + 1
            
            counter += 1
            if np.mod(counter, 200) == 0:
                save(sess, counter)
              
        #Show variables and their sizes
        show_all_variables()
      
        print("Best accuracy = %4f at epoch %2d" % (best_accuracy, best_epoch))
        print("Total time = %4.4f sec and accuracy = %4f perc" % (total_time, last_accuracy))
        
        with sqlite3.connect(database_path, check_same_thread=False) as database:
            cur = database.cursor()
            cur.execute("SELECT A_one, A_two, B_one, B_two, C_one, C_two, D_one, D_two, F_script, F_resource, current_list,\
                        url, visit_id FROM http_requests \
                        WHERE A_one IS NOT NULL AND A_two IS NOT NULL AND B_one IS NOT NULL AND B_two IS NOT NULL AND C_one IS NOT NULL AND\
                        C_two IS NOT NULL AND D_one IS NOT NULL AND D_two IS NOT NULL AND\
                        F_script IS NOT NULL AND F_resource IS NOT NULL AND current_list IS NOT NULL")
            
            rows = cur.fetchall()
            
            right = 0
            total = 0
            print(len(rows))
             
            for row in rows:
                data_row = []
                data_row.append(row[0])
                data_row.append(row[1])
                data_row.append(row[2])
                data_row.append(row[3])
                data_row.append(row[4])
                data_row.append(row[5])
                data_row.append(row[6])
                data_row.append(row[7])
                data_row.append(row[8])
                data_row.append(row[9])
                
                total += 1
                
                result = sess.run(logits,
							 feed_dict={
								 x: [data_row],
								 keep_prob: 1.
							 })
  
                result = 0 if result[0][0] < 0 else 1
                print("Pred = ", result)
                print("Correct = ", row[10])
                print()
                
                if result == row[10]:
                  right += 1
                
        #        x.append(data_row)
        #        y.append(row[10])
        #        print("DATA: ", [data_row])
        #        print("URL %s has pred %d" % (row[11], neigh.predict([data_row])))
            print("Accuracy = ", (right / total))