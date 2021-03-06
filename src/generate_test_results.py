#!/usr/bin/env python

import theano.sandbox.cuda
theano.sandbox.cuda.use('gpu0')
import sys
sys.path.append('/afs/inf.ed.ac.uk/user/s16/s1670404/vqa_human_attention/src/')
sys.path.append('/afs/inf.ed.ac.uk/user/s16/s1670404/vqa_human_attention/src/data-providers/')
sys.path.append('/afs/inf.ed.ac.uk/user/s16/s1670404/vqa_human_attention/src/models/')
from optimization_weight import *
from data_provision_att_vqa_test import *
from data_processing_vqa import *
import json
import pickle
import sys
dataDir = '/afs/inf.ed.ac.uk/group/synproc/Goncalo/VQA'
sys.path.insert(0, '%s/PythonHelperTools/vqaTools' %(dataDir))
sys.path.insert(0, '%s/PythonEvaluationTools/' %(dataDir))
from vqa import VQA
from vqaEvaluation.vqaEval import VQAEval

f = open('/afs/inf.ed.ac.uk/group/synproc/Goncalo/data_vqa/answer_dict.pkl', 'r')
answer_dict = pickle.load(f)
f.close()
answer_dict = {v: k for k, v in answer_dict.iteritems()}

model_path = sys.argv[1]
result_file_name = sys.argv[2]
model_script = sys.argv[3]

result = OrderedDict()

if model_script == 'baseline':
    from san_att_conv_twolayer_theano import *
    options, params, shared_params = load_model(model_path)
    image_feat, input_idx, input_mask, label, \
    dropout, cost, accu, pred_label, \
    prob_attention_1, prob_attention_2 = build_model(
        shared_params, options)
elif model_script=='hsan_deepfix':
    from semi_joint_hsan_deepfix_att_theano import *
    options, params, shared_params = load_model(model_path)
    options['saliency_dropout'] = 0.5
    image_feat, input_idx, input_mask, \
    label, dropout, ans_cost, accu, pred_label, \
    prob_attention_1, prob_attention_2, map_cost, map_label = build_model(shared_params, params, options)
elif model_script=='hsan':
    from semi_joint_hsan_att_theano import *
    options, params, shared_params = load_model(model_path)
    image_feat, input_idx, input_mask, \
    label, dropout, ans_cost, accu, pred_label, \
    prob_attention_1, prob_attention_2, map_cost, map_label = build_model(shared_params, options)
elif model_script=='hsan_deepfix_split':
    from multi_joint_hsan_deepfix_att_theano import *
    options, params, shared_params = load_model(model_path)
    image_feat, input_idx, input_mask, \
    label, dropout, ans_cost, accu, pred_label, \
    prob_attention_1, prob_attention_2, map_cost, \
    map_label, saliency_attention = build_model(shared_params, params, options)


f_pass = theano.function(
    inputs=[
        image_feat,
        input_idx,
        input_mask],
    outputs=[pred_label],
    on_unused_input='warn')

options['data_path'] = '/afs/inf.ed.ac.uk/group/synproc/Goncalo/data_vqa/'
options['feature_file'] = 'test_feat.h5'

data_provision_att_vqa = DataProvisionAttVqaTest(options['data_path'], options['feature_file'])

dropout.set_value(numpy.float32(0.))

i=0

for batch_image_feat, batch_question, batch_answer_label in data_provision_att_vqa.iterate_batch(
        'test', options['batch_size']):
    input_idx, input_mask = process_batch(
        batch_question, reverse=options['reverse'])
    batch_image_feat = reshape_image_feat(batch_image_feat,
                                          options['num_region'],
                                          options['region_dim'])
    [pred_label] = f_pass(
        batch_image_feat,
        np.transpose(input_idx),
        np.transpose(input_mask))
    res =[]
    for pred in pred_label:
        ans = answer_dict[pred]
        ques_id = data_provision_att_vqa._question_id['test'][i]
        i += 1
        result[ques_id] = ans

results = [result]

d = results[0]
res = []
for key, value in d.iteritems():
    res.append({'answer': value, 'question_id': int(key)})

with open('/afs/inf.ed.ac.uk/group/synproc/Goncalo/'+result_file_name, 'w') as outfile:
    json.dump(res, outfile)
