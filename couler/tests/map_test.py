import unittest

import couler.argo as couler

couler.config_workflow(name="pytest")


def consume(message):
    return couler.run_container(
        image="docker/whalesay:latest", command=["cowsay"], args=[message]
    )


class MapTest(unittest.TestCase):
    def test_map_function(self):
        test_paras = ["t1", "t2", "t3"]
        couler.map(lambda x: consume(x), test_paras)
        wf = couler.workflow_yaml()

        templates = wf["spec"]["templates"]
        self.assertEqual(len(templates), 2)

        # We should have a 'consume' template
        consume_template = templates[1]
        self.assertEqual(consume_template["name"], "consume")
        # Check input parameters
        expected_paras = [{"name": "para-consume-0"}]
        self.assertListEqual(
            consume_template["inputs"]["parameters"], expected_paras
        )
        # Check container
        expected_container = {
            "image": "docker/whalesay:latest",
            "command": ["cowsay"],
            "args": ['"{{inputs.parameters.para-consume-0}}"'],
            "env": [
                {"name": "NVIDIA_VISIBLE_DEVICES", "value": ""},
                {"name": "NVIDIA_DRIVER_CAPABILITIES", "value": ""},
            ],
        }
        self.assertDictEqual(consume_template["container"], expected_container)

        # Check the steps template
        steps_template = templates[0]
        self.assertTrue(steps_template["name"] in ["pytest", "runpy"])
        self.assertEqual(len(steps_template["steps"]), 1)
        self.assertEqual(len(steps_template["steps"][0]), 1)
        map_step = steps_template["steps"][0][0]
        self.assertIn("consume", map_step["name"])
        self.assertEqual(map_step["template"], "consume")
        # Check arguments
        expected_paras = [
            {"name": "para-consume-0", "value": '"{{item.para-consume-0}}"'}
        ]
        self.assertListEqual(
            map_step["arguments"]["parameters"], expected_paras
        )
        # Check withItems
        expected_with_items = [
            {"para-consume-0": "t1"},
            {"para-consume-0": "t2"},
            {"para-consume-0": "t3"},
        ]
        self.assertListEqual(map_step["withItems"], expected_with_items)
        couler._cleanup()

    # TODO: Provide new test case without `tf.train`.
    # def test_map_function_with_run_job(self):
    #     couler.map(
    #         lambda x: tf.train(
    #             num_ps=1,
    #             num_workers=1,
    #             command="python /opt/kubeflow/tf_smoke.py",
    #             image="couler/tf-smoke-test:v1.0",
    #             step_name=x,
    #         ),
    #         ["couler-tf-job-0", "couler-tf-job-1"],
    #     )
    #     wf = couler.workflow_yaml()
    #     templates = wf["spec"]["templates"]
    #     self.assertEqual(len(templates), 2)
    #     # Check inner steps template
    #     inner_steps_template = templates[0]["steps"][0][0]
    #     self.assertEqual(
    #         inner_steps_template["arguments"]["parameters"],
    #         [
    #             {
    #                 "name": "couler-tf-job-0-para-name",
    #                 "value": '"{{item.couler-tf-job-0-para-name}}"',
    #             }
    #         ],
    #     )
    #     self.assertEqual(
    #         inner_steps_template["withItems"],
    #         [
    #             {"couler-tf-job-0-para-name": "couler-tf-job-0"},
    #             {"couler-tf-job-0-para-name": "couler-tf-job-1"},
    #         ],
    #     )
    #     # Check training step template
    #     training_template = templates[1]
    #     self.assertEqual(
    #         training_template["inputs"]["parameters"],
    #         [{"name": "couler-tf-job-0-para-name"}],
    #     )
    #     self.assertTrue(
    #         "name: '{{inputs.parameters.couler-tf-job-0-para-name}}'"
    #         in training_template["resource"]["manifest"]
    #     )
    #     couler._cleanup()
